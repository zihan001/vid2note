# pdfmaker.py (AUTO-ADAPT + VERIFIED CAPTIONS + FALLBACK VISUALS)
# Fixes:
# - Auto-adapts when too many frames rejected (tries more candidates automatically)
# - Never mismatches screenshot & explanation (per-image verify step)
# - Rejects YouTube comments/people/random frames
# - Adds red arrows + labels on kept screenshots
# - Adds generated "visual examples" diagrams if not enough good screenshots
# - Rate-limit safe (retry/backoff)

import os
import json
import base64
import subprocess
import shutil
import time
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from openai import OpenAI, RateLimitError


# ===============================
# PATHS / FILES
# ===============================

BASE_DIR = Path(__file__).parent
KEY_FILE = BASE_DIR / "secret_key.txt"
VIDEO_FILE = BASE_DIR / "SQL_explained.mp4"
TRANSCRIPT_FILE = BASE_DIR / "SQL_explained_transcript.txt"

OUT_DIR = BASE_DIR / "out"
FRAMES_DIR = OUT_DIR / "frames"
PDF_PATH = OUT_DIR / "SQL_notes.pdf"


# ===============================
# SETTINGS
# ===============================

MODEL = "gpt-4o-mini"

# We'll try these candidate counts automatically if too many get rejected:
CANDIDATE_COUNTS_TRY = [36, 60, 90]

# Request more picks, then verify + reject
PICK_REQUEST = 18
FINAL_KEEP_TARGET = 12

# Minimum screenshots acceptable; below this, we add fallback diagrams
MIN_KEEP_OK = 4

# Image settings
HIRES_WIDTH = 1800
CAND_THUMB_WIDTH = 480

# PDF content limits
MAX_OVERVIEW = 10
MAX_CONCEPT_CARDS = 10
MAX_CHAPTERS = 8
MAX_EXAMPLES = 4
MAX_QUESTIONS = 10


# ===============================
# LOAD KEY
# ===============================

if not KEY_FILE.exists():
    raise RuntimeError("❌ secret_key.txt not found beside pdfmaker.py")

with open(KEY_FILE, "r", encoding="utf-8") as f:
    os.environ["OPENAI_API_KEY"] = f.read().strip()

if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError("❌ secret_key.txt is empty.")

client = OpenAI()


# ===============================
# RETRY / BACKOFF
# ===============================

def call_with_retries(fn, max_retries: int = 8):
    delay = 2.0
    for _ in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            time.sleep(delay)
            delay = min(delay * 1.8, 30.0)
    raise RuntimeError("❌ Still rate-limited. Wait ~30s and run again.")


# ===============================
# HELPERS
# ===============================

def ensure_tools():
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("❌ ffmpeg not found on PATH.")
    if shutil.which("ffprobe") is None:
        raise RuntimeError("❌ ffprobe not found on PATH.")

def ensure_dirs():
    OUT_DIR.mkdir(exist_ok=True)
    FRAMES_DIR.mkdir(exist_ok=True)

def read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def img_to_data_url(path: Path) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

def get_video_duration_seconds(video_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)

def clear_dir_jpgs(folder: Path, prefix: str):
    for f in folder.glob(f"{prefix}*.jpg"):
        try:
            f.unlink()
        except Exception:
            pass

def sec_to_mmss(sec: float) -> str:
    s = int(round(sec))
    m = s // 60
    s = s % 60
    return f"{m:02d}:{s:02d}"


# ===============================
# FRAME EXTRACTION
# ===============================

def extract_candidate_thumbs(video_path: Path, out_dir: Path, count: int) -> List[Tuple[float, Path]]:
    clear_dir_jpgs(out_dir, "cand_")

    dur = get_video_duration_seconds(video_path)
    if dur <= 0:
        raise RuntimeError("❌ Could not read video duration")

    times = [dur * (i + 1) / (count + 2) for i in range(count)]

    results = []
    for i, t in enumerate(times, start=1):
        out_path = out_dir / f"cand_{i:03d}.jpg"
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{t:.3f}",
            "-i", str(video_path),
            "-frames:v", "1",
            "-vf", f"scale={CAND_THUMB_WIDTH}:-1",
            "-q:v", "8",
            str(out_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        results.append((t, out_path))
    return results


def pick_best_frames_with_gpt(transcript: str, candidates: List[Tuple[float, Path]], pick_n: int) -> List[Dict[str, Any]]:
    t = transcript.strip()
    if len(t) > 2000:
        t = t[:2000] + "\n…(trimmed)…"

    time_list = [round(ts, 2) for ts, _ in candidates]

    content = [{
        "type": "input_text",
        "text": (
            "Select the BEST frames for SQL study notes.\n"
            f"Return EXACTLY {pick_n} selections.\n\n"
            "STRICT DO-NOT-SELECT (reject):\n"
            "- YouTube comments/replies/profile pics/like buttons/'REPLY'\n"
            "- people/talking head/memes/sports\n"
            "- random logos / decorative animation\n"
            "- blurred/blank\n\n"
            "Prefer:\n"
            "- ERD diagrams\n"
            "- tables/columns (id, name, etc.)\n"
            "- code snippets\n"
            "- slides naming SQL concepts\n\n"
            f"Timestamps aligned to images: {time_list}\n\n"
            "Return VALID JSON ONLY:\n"
            "{\"selected\":[{\"time\":12.34,\"hint\":\"short reason\"}]}\n\n"
            "Transcript context:\n"
            f"{t}\n"
        )
    }]

    for _, path in candidates:
        content.append({"type": "input_image", "image_url": img_to_data_url(path)})

    resp = call_with_retries(lambda: client.responses.create(
        model=MODEL,
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_object"}}
    ))

    data = json.loads(resp.output_text)
    selected = data.get("selected", [])
    if not isinstance(selected, list) or len(selected) == 0:
        return []
    return selected


def extract_high_res_frames(video_path: Path, out_dir: Path, selected: List[Dict[str, Any]]) -> List[Tuple[float, Path]]:
    clear_dir_jpgs(out_dir, "best_raw_")
    out = []
    for i, item in enumerate(selected, start=1):
        t = float(item["time"])
        out_path = out_dir / f"best_raw_{i:02d}.jpg"
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{t:.3f}",
            "-i", str(video_path),
            "-frames:v", "1",
            "-vf", f"scale={HIRES_WIDTH}:-1",
            "-q:v", "2",
            str(out_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        out.append((t, out_path))
    return out


# ===============================
# VERIFY + ANNOTATE (ACCURACY)
# ===============================

def draw_red_arrows(src_path: Path, dst_path: Path, arrows: List[Dict[str, Any]]):
    img = Image.open(src_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    def clamp(v):
        return max(0.0, min(1.0, float(v)))

    for a in (arrows or [])[:6]:
        frm = a.get("from", [0.1, 0.1])
        to = a.get("to", [0.2, 0.2])
        text = str(a.get("text", "")).strip()

        x1 = int(clamp(frm[0]) * W)
        y1 = int(clamp(frm[1]) * H)
        x2 = int(clamp(to[0]) * W)
        y2 = int(clamp(to[1]) * H)

        draw.line((x1, y1, x2, y2), fill=(255, 0, 0), width=6)

        ang = math.atan2(y2 - y1, x2 - x1)
        head_len = 22
        left = (x2 - head_len * math.cos(ang - 0.5), y2 - head_len * math.sin(ang - 0.5))
        right = (x2 - head_len * math.cos(ang + 0.5), y2 - head_len * math.sin(ang + 0.5))
        draw.polygon([(x2, y2), left, right], fill=(255, 0, 0))

        if text:
            tx, ty = x1, y1
            pad = 6
            bbox = draw.textbbox((tx, ty), text, font=font)
            bx1, by1, bx2, by2 = bbox
            draw.rectangle((bx1 - pad, by1 - pad, bx2 + pad, by2 + pad), fill=(255, 255, 255))
            draw.text((tx, ty), text, fill=(255, 0, 0), font=font)

    img.save(dst_path, quality=95)


def verify_and_annotate_frames(transcript: str, frames: List[Tuple[float, Path]], keep_target: int) -> List[Dict[str, Any]]:
    t = transcript.strip()
    if len(t) > 3500:
        t = t[:3500] + "\n…(trimmed)…"

    clear_dir_jpgs(FRAMES_DIR, "best_annot_")
    results = []

    for (time_sec, img_path) in frames:
        prompt = (
            "Verify this screenshot for SQL notes.\n"
            "If it shows YouTube comments/replies, profile icons, 'REPLY', likes/dislikes: skip=true.\n"
            "If it is just decorative animation/logo without SQL content: skip=true.\n"
            "Otherwise skip=false.\n\n"
            "If skip=false, generate an accurate title/caption/explanation based ONLY on what is visible.\n"
            "Also return 1-4 arrows pointing to the key things (normalized coords).\n\n"
            "Return JSON ONLY:\n"
            "{"
            "\"skip\":false,"
            "\"title\":\"specific title\","
            "\"caption\":\"what is visible\","
            "\"explain_like_student\":\"2-5 sentences\","
            "\"arrows\":[{\"from\":[0.1,0.1],\"to\":[0.2,0.2],\"text\":\"label\"}]"
            "}"
        )

        resp = call_with_retries(lambda: client.responses.create(
            model=MODEL,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": img_to_data_url(img_path)}
                ]
            }],
            text={"format": {"type": "json_object"}}
        ))

        meta = json.loads(resp.output_text)
        if meta.get("skip", False):
            continue

        annotated_path = FRAMES_DIR / f"best_annot_{len(results)+1:02d}.jpg"
        draw_red_arrows(img_path, annotated_path, meta.get("arrows", []))

        results.append({
            "time_sec": time_sec,
            "time": sec_to_mmss(time_sec),
            "image_path": annotated_path,
            "title": meta.get("title", "Screenshot"),
            "caption": meta.get("caption", ""),
            "explain_like_student": meta.get("explain_like_student", "")
        })

        if len(results) >= keep_target:
            break

    return results


# ===============================
# TEXT NOTES (TRANSCRIPT ONLY)
# ===============================

def generate_text_notes(transcript: str) -> Dict[str, Any]:
    t = transcript.strip()
    if len(t) > 8000:
        t = t[:8000] + "\n…(trimmed)…"

    schema = {
        "title": "string",
        "overview": ["string"],
        "concept_cards": [{"term": "string", "explanation": "string", "why_it_matters": "string"}],
        "chapters": [{"heading": "string", "summary": "string", "bullets": ["string"]}],
        "examples": [{"title": "string", "sql": "string", "explanation": "string"}],
        "key_timestamps": [{"time": "MM:SS", "why_important": "string"}],
        "practice_questions": ["string"]
    }

    prompt = f"""
Create beginner-friendly SQL study notes from the transcript.

Rules:
- Don’t copy transcript lines verbatim.
- Add 2–4 simple SQL examples.
- Output VALID JSON ONLY.

Transcript:
{t}

Return JSON matching:
{json.dumps(schema, ensure_ascii=False)}
""".strip()

    resp = call_with_retries(lambda: client.responses.create(
        model=MODEL,
        input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        text={"format": {"type": "json_object"}}
    ))
    notes = json.loads(resp.output_text)
    notes.setdefault("title", "Video Notes")
    notes.setdefault("overview", [])
    notes.setdefault("concept_cards", [])
    notes.setdefault("chapters", [])
    notes.setdefault("examples", [])
    notes.setdefault("key_timestamps", [])
    notes.setdefault("practice_questions", [])
    return notes


# ===============================
# FALLBACK VISUALS (GENERATED DIAGRAMS)
# ===============================

def make_fallback_diagrams(out_dir: Path) -> List[Dict[str, Any]]:
    """
    Creates simple visuals (ERD + table with PK/FK) so the PDF stays visual even if the video doesn't.
    """
    imgs = []

    # 1) Simple ERD diagram
    p1 = out_dir / "fallback_erd.jpg"
    img = Image.new("RGB", (1400, 800), (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("arial.ttf", 38)
        font = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font_big = ImageFont.load_default()
        font = ImageFont.load_default()

    d.text((40, 30), "Visual Example: ERD (Customers → Orders)", fill=(0, 0, 0), font=font_big)

    # boxes
    cust = (120, 180, 600, 560)
    order = (800, 180, 1280, 560)
    d.rectangle(cust, outline=(0, 0, 0), width=4)
    d.rectangle(order, outline=(0, 0, 0), width=4)

    d.text((cust[0]+20, cust[1]+20), "Customers", fill=(0, 0, 0), font=font_big)
    d.text((cust[0]+20, cust[1]+90), "customer_id (PK)", fill=(255, 0, 0), font=font)
    d.text((cust[0]+20, cust[1]+130), "name", fill=(0, 0, 0), font=font)
    d.text((cust[0]+20, cust[1]+170), "email", fill=(0, 0, 0), font=font)

    d.text((order[0]+20, order[1]+20), "Orders", fill=(0, 0, 0), font=font_big)
    d.text((order[0]+20, order[1]+90), "order_id (PK)", fill=(255, 0, 0), font=font)
    d.text((order[0]+20, order[1]+130), "customer_id (FK)", fill=(255, 0, 0), font=font)
    d.text((order[0]+20, order[1]+170), "order_date", fill=(0, 0, 0), font=font)

    # arrow relationship
    d.line((600, 370, 800, 370), fill=(255, 0, 0), width=8)
    d.polygon([(800, 370), (770, 350), (770, 390)], fill=(255, 0, 0))
    d.text((640, 320), "1 to many", fill=(255, 0, 0), font=font)

    img.save(p1, quality=95)
    imgs.append({
        "time_sec": None,
        "time": "N/A",
        "image_path": p1,
        "title": "ERD Example: Customers → Orders",
        "caption": "A simple ER diagram showing a one-to-many relationship.",
        "explain_like_student": "A primary key (PK) uniquely identifies rows in a table. A foreign key (FK) stores the PK from another table to create a relationship."
    })

    return imgs


# ===============================
# PDF
# ===============================

def draw_wrapped(c: canvas.Canvas, x: float, y: float, text: str, max_width: float, font="Helvetica", size=11, leading=14) -> float:
    c.setFont(font, size)
    words = (text or "").split()
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        if c.stringWidth(test, font, size) <= max_width:
            line = test
        else:
            c.drawString(x, y, line)
            y -= leading
            line = w
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y

def draw_code_block(c: canvas.Canvas, x: float, y: float, code: str, max_width: float) -> float:
    code = (code or "").strip("\n")
    if not code:
        return y
    c.setFont("Courier", 9)
    char_w = c.stringWidth("M", "Courier", 9)
    max_chars = max(20, int(max_width / char_w))
    for raw_line in code.splitlines():
        line = raw_line.rstrip("\n")
        while len(line) > max_chars:
            c.drawString(x, y, line[:max_chars])
            y -= 12
            line = line[max_chars:]
        c.drawString(x, y, line)
        y -= 12
    return y

def generate_pdf(text_notes: Dict[str, Any], screenshots: List[Dict[str, Any]]):
    c = canvas.Canvas(str(PDF_PATH), pagesize=letter)
    W, H = letter
    margin = 0.75 * inch
    x = margin
    y = H - margin
    max_w = W - 2 * margin

    def new_page():
        nonlocal y
        c.showPage()
        y = H - margin

    # title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x, y, text_notes.get("title", "Video Notes"))
    y -= 26

    # overview
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x, y, "Overview")
    y -= 18
    for b in text_notes.get("overview", [])[:MAX_OVERVIEW]:
        if y < margin + 80:
            new_page()
        y = draw_wrapped(c, x, y, f"• {b}", max_w)
    y -= 8

    # concepts
    cards = text_notes.get("concept_cards", [])[:MAX_CONCEPT_CARDS]
    if cards:
        if y < margin + 140:
            new_page()
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x, y, "Core Concepts")
        y -= 18
        for card in cards:
            if y < margin + 120:
                new_page()
            term = str(card.get("term", "")).strip()
            expl = str(card.get("explanation", "")).strip()
            why = str(card.get("why_it_matters", "")).strip()
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, term)
            y -= 14
            y = draw_wrapped(c, x, y, expl, max_w)
            if why:
                y = draw_wrapped(c, x, y, f"Why it matters: {why}", max_w, font="Helvetica-Oblique", size=11)
            y -= 6

    # examples
    examples = text_notes.get("examples", [])[:MAX_EXAMPLES]
    if examples:
        new_page()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "Examples")
        y -= 20
        for ex in examples:
            if y < margin + 180:
                new_page()
            title = str(ex.get("title", "Example")).strip()
            sql = str(ex.get("sql", "")).strip()
            expl = str(ex.get("explanation", "")).strip()
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, title)
            y -= 14
            y = draw_wrapped(c, x, y, expl, max_w)
            y -= 4
            y = draw_code_block(c, x, y, sql, max_w)
            y -= 10

    # screenshots
    if screenshots:
        new_page()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "Important Visuals (Verified)")
        y -= 20

        max_img_h = 3.9 * inch
        for idx, s in enumerate(screenshots, start=1):
            if y < margin + max_img_h + 150:
                new_page()
            title = s["title"]
            time_str = s.get("time", "N/A")
            img_path = s["image_path"]

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, f"{idx}. {title} ({time_str})")
            y -= 14

            try:
                im = Image.open(img_path)
                iw, ih = im.size
                scale = min(max_w / iw, max_img_h / ih)
                dw, dh = iw * scale, ih * scale
                c.drawInlineImage(str(img_path), x, y - dh, dw, dh)
                y -= dh + 10
            except Exception:
                c.setFont("Helvetica", 11)
                c.drawString(x, y, f"[Could not render image: {Path(img_path).name}]")
                y -= 14

            cap = s.get("caption", "").strip()
            expl = s.get("explain_like_student", "").strip()
            if cap:
                y = draw_wrapped(c, x, y, f"Caption: {cap}", max_w)
            if expl:
                y = draw_wrapped(c, x, y, f"Explanation: {expl}", max_w)
            y -= 10

    c.save()


# ===============================
# ORCHESTRATION
# ===============================

def build_verified_screenshots(transcript: str) -> List[Dict[str, Any]]:
    """
    Try multiple passes with increasing candidate counts until we get enough verified screenshots.
    """
    for cand_count in CANDIDATE_COUNTS_TRY:
        candidates = extract_candidate_thumbs(VIDEO_FILE, FRAMES_DIR, count=cand_count)
        picked = pick_best_frames_with_gpt(transcript, candidates, pick_n=PICK_REQUEST)
        if not picked:
            continue
        raw = extract_high_res_frames(VIDEO_FILE, FRAMES_DIR, picked)
        verified = verify_and_annotate_frames(transcript, raw, keep_target=FINAL_KEEP_TARGET)

        if len(verified) >= MIN_KEEP_OK:
            return verified

    return []


def main():
    ensure_tools()
    ensure_dirs()

    if not VIDEO_FILE.exists():
        raise RuntimeError(f"❌ Missing video: {VIDEO_FILE.name}")
    if not TRANSCRIPT_FILE.exists():
        raise RuntimeError(f"❌ Missing transcript: {TRANSCRIPT_FILE.name}")

    transcript = read_text(TRANSCRIPT_FILE)

    # Verified screenshots (might be few if video is mostly animation)
    screenshots = build_verified_screenshots(transcript)

    # If too few, add generated visuals
    if len(screenshots) < MIN_KEEP_OK:
        screenshots.extend(make_fallback_diagrams(OUT_DIR))

    text_notes = generate_text_notes(transcript)

    generate_pdf(text_notes, screenshots)

    print(f"✅ PDF created: {PDF_PATH}")


if __name__ == "__main__":
    main()
