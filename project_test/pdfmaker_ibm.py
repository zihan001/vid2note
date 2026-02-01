# pdfmaker_ibm_watsonx.py
# Uses IBM watsonx.ai (Toronto) with an IBM Cloud API key stored in ./api_key_watsonx (or .txt)

import os
import json
import base64
import subprocess
import shutil
import time
import math
import re
import ast
from pathlib import Path
from typing import List, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference


# ===============================
# CONFIG (NO ENV VARS)
# ===============================

BASE_DIR = Path(__file__).parent

# Accept either api_key_watsonx OR api_key_watsonx.txt (Windows hides extensions)
TOKEN_FILE = BASE_DIR / "api_key_watsonx"
if not TOKEN_FILE.exists():
    TOKEN_FILE = BASE_DIR / "api_key_watsonx.txt"

# watsonx.ai Runtime base URL for Toronto
WATSONX_URL = "https://ca-tor.ml.cloud.ibm.com"

# Your watsonx.ai project id
WATSONX_PROJECT_ID = "22993cfa-7fc1-499e-8670-9d2a90ea8c72"

# Models (must be available in your watsonx project)
VISION_MODEL_ID = "meta-llama/llama-3-2-11b-vision-instruct"
TEXT_MODEL_ID = "meta-llama/llama-3-3-70b-instruct"


# ===============================
# INPUT FILES
# ===============================

VIDEO_FILE = BASE_DIR / "SQL_explained.mp4"
TRANSCRIPT_FILE = BASE_DIR / "SQL_explained_transcript.txt"

OUT_DIR = BASE_DIR / "out"
FRAMES_DIR = OUT_DIR / "frames"
PDF_PATH = OUT_DIR / "SQL_notes.pdf"


# ===============================
# PIPELINE SETTINGS
# ===============================

CANDIDATE_COUNTS_TRY = [36, 60, 90]
PICK_REQUEST = 18
FINAL_KEEP_TARGET = 12
MIN_KEEP_OK = 4

HIRES_WIDTH = 1800
CAND_THUMB_WIDTH = 480

MAX_OVERVIEW = 10
MAX_CONCEPT_CARDS = 10
MAX_EXAMPLES = 4


# ===============================
# AUTH / MODELS
# ===============================

if not TOKEN_FILE.exists():
    raise RuntimeError("❌ api_key_watsonx (or api_key_watsonx.txt) not found beside the script.")

WATSONX_APIKEY = TOKEN_FILE.read_text(encoding="utf-8").strip()
if not WATSONX_APIKEY:
    raise RuntimeError("❌ api_key_watsonx is empty. Paste your IBM Cloud API KEY in it (one line only).")

credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_APIKEY)

vision_model = ModelInference(
    model_id=VISION_MODEL_ID,
    credentials=credentials,
    project_id=WATSONX_PROJECT_ID,
    params={"max_tokens": 900, "temperature": 0.2}
)

text_model = ModelInference(
    model_id=TEXT_MODEL_ID,
    credentials=credentials,
    project_id=WATSONX_PROJECT_ID,
    params={"max_tokens": 1600, "temperature": 0.2}
)


# ===============================
# RETRY
# ===============================

def call_with_retries(fn, max_retries: int = 8):
    delay = 2.0
    last_err = None
    for _ in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            time.sleep(delay)
            delay = min(delay * 1.8, 25.0)
    raise RuntimeError(f"❌ watsonx call failed after retries: {last_err}")


# ===============================
# UTIL
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
    return path.read_text(encoding="utf-8", errors="ignore")

def img_to_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")

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
# WATSONX CHAT HELPERS
# ===============================

def wx_chat_text_only(prompt: str) -> str:
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    resp = call_with_retries(lambda: text_model.chat(messages=messages))
    return resp["choices"][0]["message"]["content"]

def wx_chat_with_one_image(prompt: str, image_path: Path) -> str:
    img_b64 = img_to_b64(image_path)
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
    }]
    resp = call_with_retries(lambda: vision_model.chat(messages=messages))
    return resp["choices"][0]["message"]["content"]


# ===============================
# ROBUST JSON PARSER
# ===============================

def parse_json_strict(s: str) -> Any:
    """
    Robust JSON extractor for LLM outputs:
    - extracts {...} if extra text
    - fixes trailing commas
    - handles python-dict style output via ast.literal_eval
    - final fallback: repair with text_model
    """
    raw_all = (s or "").strip()

    # Extract first {...}
    first = raw_all.find("{")
    last = raw_all.rfind("}")
    raw = raw_all[first:last+1] if (first != -1 and last != -1 and last > first) else raw_all

    # Remove trailing commas
    raw = re.sub(r",\s*([}\]])", r"\1", raw)

    # Try strict JSON
    try:
        return json.loads(raw)
    except Exception:
        pass

    # Try python-literal (handles single quotes + True/False)
    try:
        return ast.literal_eval(raw)
    except Exception:
        pass

    # Last resort: ask text model to convert to valid JSON ONLY
    repair_prompt = (
        "Convert the following into VALID JSON ONLY.\n"
        "Rules:\n"
        "- output only JSON\n"
        "- use double quotes for keys and string values\n\n"
        f"{raw_all}"
    )
    repaired = wx_chat_text_only(repair_prompt).strip()

    first = repaired.find("{")
    last = repaired.rfind("}")
    repaired = repaired[first:last+1] if (first != -1 and last != -1 and last > first) else repaired
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    return json.loads(repaired)


# ===============================
# FRAMES
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


def pick_best_frames_with_watsonx(transcript: str, candidates: List[Tuple[float, Path]], pick_n: int) -> List[Dict[str, Any]]:
    """
    watsonx vision model in your region allows only 1 image per request,
    so we score each candidate individually, then pick top N.
    """
    t = transcript.strip()
    if len(t) > 2000:
        t = t[:2000] + "\n…(trimmed)…"

    scored = []

    for (time_sec, img_path) in candidates:
        prompt = (
            "You are selecting screenshots for SQL study notes.\n"
            "Look at the image and rate how useful it is.\n\n"
            "Reject (score=0 and reject=true) if it shows:\n"
            "- YouTube comments/replies/profile pics/like buttons/'REPLY'\n"
            "- people/talking head/memes/sports\n"
            "- decorative animation/logo without SQL content\n"
            "- blurry/blank\n\n"
            "Prefer (high score) if it shows:\n"
            "- ERD diagram\n"
            "- tables/columns\n"
            "- SQL code\n"
            "- slide naming SQL concepts\n\n"
            "Return VALID JSON ONLY (double quotes only):\n"
            "{\"score\":7,\"reject\":false,\"reason\":\"short reason\",\"tags\":[\"erd\",\"table\",\"code\",\"concept\",\"comment\",\"logo\"]}\n\n"
            "Transcript context:\n"
            f"{t}\n"
        )

        try:
            out = wx_chat_with_one_image(prompt, img_path)
            data = parse_json_strict(out)
            score = float(data.get("score", 0))
            reject = bool(data.get("reject", False))
            reason = str(data.get("reason", "")).strip()
        except Exception:
            score, reject, reason = 0.0, True, "parse/error"

        if reject:
            continue

        scored.append({
            "time": float(time_sec),
            "hint": reason,
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:pick_n]


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
# VERIFY + ANNOTATE
# ===============================

def draw_red_arrows(src_path: Path, dst_path: Path, arrows):
    img = Image.open(src_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    # Normalize arrows into a list of dicts
    if arrows is None:
        arrows_list = []
    elif isinstance(arrows, list):
        arrows_list = arrows
    elif isinstance(arrows, dict):
        # could be a single arrow dict or {"0":{...},"1":{...}}
        if "from" in arrows and "to" in arrows:
            arrows_list = [arrows]
        else:
            arrows_list = [v for v in arrows.values() if isinstance(v, dict)]
    else:
        arrows_list = []

    def clamp(v):
        return max(0.0, min(1.0, float(v)))

    for a in arrows_list[:6]:
        frm = a.get("from", [0.1, 0.1])
        to = a.get("to", [0.2, 0.2])
        text = str(a.get("text", "")).strip()

        try:
            x1 = int(clamp(frm[0]) * W)
            y1 = int(clamp(frm[1]) * H)
            x2 = int(clamp(to[0]) * W)
            y2 = int(clamp(to[1]) * H)
        except Exception:
            continue

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


def verify_and_annotate_frames(frames: List[Tuple[float, Path]], keep_target: int) -> List[Dict[str, Any]]:
    clear_dir_jpgs(FRAMES_DIR, "best_annot_")
    results = []

    for (time_sec, img_path) in frames:
        prompt = (
            "Verify this screenshot for SQL notes.\n"
            "If it shows YouTube comments/replies, profile icons, 'REPLY', likes/dislikes: skip=true.\n"
            "If it is just decorative animation/logo without SQL content: skip=true.\n"
            "Otherwise skip=false.\n\n"
            "If skip=false, generate an accurate title/caption/explanation based ONLY on what is visible.\n"
            "Also return 1-4 arrows pointing to key things (normalized coords).\n\n"
            "Return VALID JSON ONLY (double quotes only):\n"
            "{"
            "\"skip\":false,"
            "\"title\":\"specific title\","
            "\"caption\":\"what is visible\","
            "\"explain_like_student\":\"2-5 sentences\","
            "\"arrows\":[{\"from\":[0.1,0.1],\"to\":[0.2,0.2],\"text\":\"label\"}]"
            "}"
        )

        out = wx_chat_with_one_image(prompt, img_path)
        meta = parse_json_strict(out)

        # If meta is not a dict, skip safely
        if not isinstance(meta, dict):
            continue

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
# NOTES (TRANSCRIPT)
# ===============================

def generate_text_notes(transcript: str) -> Dict[str, Any]:
    t = transcript.strip()
    if len(t) > 8000:
        t = t[:8000] + "\n…(trimmed)…"

    schema = {
        "title": "string",
        "overview": ["string"],
        "concept_cards": [{"term": "string", "explanation": "string", "why_it_matters": "string"}],
        "examples": [{"title": "string", "sql": "string", "explanation": "string"}],
    }

    prompt = f"""
Create beginner-friendly SQL study notes from the transcript.

Rules:
- Don’t copy transcript lines verbatim.
- Add 2–4 simple SQL examples.
- Output VALID JSON ONLY (double quotes only).

Transcript:
{t}

Return JSON matching:
{json.dumps(schema, ensure_ascii=False)}
""".strip()

    out = wx_chat_text_only(prompt)
    notes = parse_json_strict(out)

    if not isinstance(notes, dict):
        notes = {}

    notes.setdefault("title", "Video Notes")
    notes.setdefault("overview", [])
    notes.setdefault("concept_cards", [])
    notes.setdefault("examples", [])
    return notes


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

    c.setFont("Helvetica-Bold", 18)
    c.drawString(x, y, text_notes.get("title", "Video Notes"))
    y -= 26

    c.setFont("Helvetica-Bold", 13)
    c.drawString(x, y, "Overview")
    y -= 18
    for b in text_notes.get("overview", [])[:MAX_OVERVIEW]:
        if y < margin + 80:
            new_page()
        y = draw_wrapped(c, x, y, f"• {b}", max_w)
    y -= 8

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

    examples = text_notes.get("examples", [])[:MAX_EXAMPLES]
    if examples:
        new_page()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "Examples")
        y -= 20
        for ex in examples:
            if y < margin + 160:
                new_page()
            title = str(ex.get("title", "Example")).strip()
            sql = str(ex.get("sql", "")).strip()
            expl = str(ex.get("explanation", "")).strip()
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, title)
            y -= 14
            y = draw_wrapped(c, x, y, expl, max_w)
            y -= 10
            c.setFont("Courier", 9)
            for line in sql.splitlines():
                if y < margin + 60:
                    new_page()
                    c.setFont("Courier", 9)
                c.drawString(x, y, line[:140])
                y -= 12
            y -= 10

    if screenshots:
        new_page()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "Important Visuals (Verified)")
        y -= 20

        max_img_h = 3.9 * inch
        for idx, s in enumerate(screenshots, start=1):
            if y < margin + max_img_h + 150:
                new_page()

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, f"{idx}. {s['title']} ({s.get('time','N/A')})")
            y -= 14

            img_path = s["image_path"]
            im = Image.open(img_path)
            iw, ih = im.size
            scale = min(max_w / iw, max_img_h / ih)
            dw, dh = iw * scale, ih * scale
            c.drawInlineImage(str(img_path), x, y - dh, dw, dh)
            y -= dh + 10

            cap = (s.get("caption") or "").strip()
            expl = (s.get("explain_like_student") or "").strip()
            if cap:
                y = draw_wrapped(c, x, y, f"Caption: {cap}", max_w)
            if expl:
                y = draw_wrapped(c, x, y, f"Explanation: {expl}", max_w)
            y -= 10

    c.save()


# ===============================
# MAIN
# ===============================

def build_verified_screenshots(transcript: str) -> List[Dict[str, Any]]:
    for cand_count in CANDIDATE_COUNTS_TRY:
        candidates = extract_candidate_thumbs(VIDEO_FILE, FRAMES_DIR, count=cand_count)
        picked = pick_best_frames_with_watsonx(transcript, candidates, pick_n=PICK_REQUEST)
        if not picked:
            continue
        raw = extract_high_res_frames(VIDEO_FILE, FRAMES_DIR, picked)
        verified = verify_and_annotate_frames(raw, keep_target=FINAL_KEEP_TARGET)
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

    screenshots = build_verified_screenshots(transcript)
    notes = generate_text_notes(transcript)

    generate_pdf(notes, screenshots)

    print(f"✅ PDF created: {PDF_PATH}")


if __name__ == "__main__":
    main()
