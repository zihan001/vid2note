# PROJECT_CONTEXT.md

## Vid2Note

AI Video → Study PDF + Interactive Tutor

---

## High-Level Goal

Build a system that converts **educational videos + transcripts** into a **high-quality, visual-first study PDF**, and then allows users to **interact with and explicitly update that PDF via chat**.

This is **not** a generic summarizer or chatbot.

Core principles:

* Visual understanding is mandatory
* Image ↔ explanation alignment must be verified
* PDF edits are explicit and versioned
* Tutor mode and editor mode are strictly separated

---

## Core Product Concept

The product has two major phases:

### Phase 1 — Study PDF Generation

User uploads:

* Video file (.mp4)
* Transcript (.txt)

The system:

* Extracts frames from the video
* Selects only meaningful educational visuals
* Verifies what each image actually shows
* Generates grounded explanations and examples
* Annotates images (arrows, labels)
* Produces a structured study PDF (v1)

### Phase 2 — Interaction

After the PDF exists, the user can:

1. Ask questions about the content (Tutor mode)
2. Explicitly request updates to the PDF (Editor mode)

---

## Key Design Constraints (Very Important)

### 1. Image Verification Before Explanation

The LLM must:

* Evaluate each image independently
* Decide whether it is educational
* Describe only what is visible
* Assign a confidence score

If an image cannot be verified, it must be rejected.

This prevents hallucinated explanations.

---

### 2. Explicit PDF Edit Trigger

The PDF is **never modified implicitly**.

Edit mode is activated only when the user includes the exact phrase:

> "create update to pdf"

Without this phrase:

* The system operates in Tutor (Q&A) mode only
* No PDF changes occur

All edits:

* Generate a new PDF version (v2, v3, …)
* Preserve previous versions

---

### 3. Versioning Is Mandatory

* Every PDF has a version number
* Older versions are never overwritten
* Chat context is scoped to the active PDF version

---

## User Flow Summary

1. User uploads video + transcript
2. System processes and generates PDF v1
3. User views/downloads PDF
4. User asks questions (Tutor mode)
5. User explicitly requests changes (Editor mode)
6. System generates new PDF version

---

## Architecture Overview

### Frontend

* Upload screen
* Processing status screen
* PDF viewer
* Chat interface
* Version selector

### Backend

* FastAPI (Python)
* ffmpeg for video processing
* Image annotation module (PIL / OpenCV)
* PDF generation service
* Storage for files and metadata

### LLM Layer

* IBM watsonx.ai
* Used for:

  * frame evaluation
  * image verification
  * explanation generation
  * example generation
  * tutor responses
  * edit instruction parsing

LLMs do **not** execute code.

---

## Pipeline Breakdown

### 1. Upload & Job Management

* Validate uploads
* Assign job ID
* Track job state:

  * UPLOADED
  * PROCESSING
  * FAILED
  * COMPLETED

---

### 2. Frame Extraction

* Extract frames using ffmpeg
* Use uniform sampling and/or scene detection
* Store timestamps

---

### 3. Frame Pre-Filtering

* Remove:

  * duplicates
  * very low-quality frames
  * near-black frames

---

### 4. Image Verification (Critical)

For each candidate frame, the LLM determines:

* Is this educational?
* What exactly is visible?
* Confidence score

Only high-confidence, relevant images continue.

---

### 5. Explanation & Example Generation

For each verified image:

* Generate explanation grounded in visible content
* Generate 1–2 examples
* Do not reference unseen elements

---

### 6. Image Annotation

* LLM outputs structured annotation instructions
* Backend renders arrows and labels on images

---

### 7. PDF Assembly

* Structured sections
* Image + explanation pairing
* Embedded metadata:

  * version number
  * generation timestamp

---

## Chat System Behavior

### Tutor Mode (Default)

* Answers questions using PDF content
* Retrieves relevant sections
* Uses external knowledge only to clarify
* Rejects off-topic questions

### Editor Mode (Explicit)

Triggered only by:

> "create update to pdf"

Capabilities:

* Add examples
* Expand explanations
* Add sections/pages

Results:

* New PDF version generated
* Previous versions preserved

---

## Non-Goals

* Not a generic chatbot
* Not a real-time tutor
* Not an LMS
* Not collaborative editing (MVP)

---

## Engineering Priorities

1. Image verification accuracy
2. Explicit edit safety
3. High-quality PDFs
4. Version integrity

If trade-offs are required, prioritize correctness and trust over speed or features.

---

## Mental Model (For AI Assistants)

Think of this system as:

* A **visual-first study note generator**
* With a **scoped tutor**
* And a **controlled document editor**

Never assume:

* Images are self-explanatory
* The PDF can be edited implicitly
* External knowledge can expand scope beyond the PDF
