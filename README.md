# Vid2Note

🎥 → 📚 AI-Powered Video to Study PDF Converter with Interactive Tutor

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

Vid2Note transforms educational videos into high-quality, visual-first study PDFs with an integrated AI tutor that can both answer questions and explicitly edit the document on command

Vid2Note transforms educational videos into high-quality, visual-first study PDFs with an integrated AI tutor that can both answer questions and explicitly edit the document on command.

### Key Features

- 🖼️ **Visual-First Learning**: Extracts and verifies meaningful educational frames
- 🤖 **AI Verification**: Prevents hallucinations by validating each image before generating explanations
- 📝 **Smart Annotations**: Automatically adds arrows, labels, and highlights to images
- 💬 **Dual-Mode Chat**: 
  - **Tutor Mode**: Ask questions about the content
  - **Editor Mode**: Explicitly update the PDF with "create update to pdf"
- 📚 **Version Control**: All PDF versions preserved (v1, v2, v3...)
- 🎯 **Grounded Content**: Explanations strictly tied to visible elements

### What Makes This Different?

Unlike generic summarizers or chatbots, Vid2Note:
- **Never modifies PDFs implicitly** - requires explicit trigger phrase
- **Validates every image** before generating content
- **Preserves all versions** - never overwrites previous PDFs
- **Strictly scopes knowledge** - tutor answers from PDF content only

---

## Quick Start

### Prerequisites

- Python 3.11+
- ffmpeg (for video processing)
- IBM watsonx.ai API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/zihan001/vid2note.git
   cd vid2note
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   cd backend
   python -m app.main
   ```

   Server will start at `http://localhost:8000`
   
   API docs available at `http://localhost:8000/docs`

---

## Project Structure

```
vid2note/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── models/       # Pydantic data models
│   │   ├── services/     # Business logic
│   │   ├── utils/        # Helper functions
│   │   ├── config.py     # Configuration management
│   │   └── main.py       # FastAPI application
│   ├── tests/            # Test suite
│   └── requirements.txt
├── frontend/             # Frontend (TBD)
├── storage/              # File storage
│   ├── videos/
│   ├── transcripts/
│   ├── frames/
│   └── pdfs/
├── pdfmaker.py          # Original prototype
├── PROJECT_PLAN.md      # Detailed development plan
└── README.md
```

---

## API Endpoints

### Upload
- `POST /api/v1/upload` - Upload video + transcript

### Jobs
- `GET /api/v1/jobs/{job_id}` - Get job status
- `DELETE /api/v1/jobs/{job_id}` - Cancel job

### Chat
- `POST /api/v1/chat` - Chat with tutor or request edits

### Versions
- `GET /api/v1/jobs/{job_id}/versions` - List all PDF versions
- `GET /api/v1/jobs/{job_id}/versions/{version_id}/download` - Download PDF

---

## Usage Flow

### 1. Upload Video & Transcript
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "video=@lecture.mp4" \
  -F "transcript=@lecture.txt"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Files uploaded successfully. Processing started."
}
```

### 2. Check Processing Status
```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress_percentage": 45,
  "current_stage": "Verifying images"
}
```

### 3. Chat - Tutor Mode (Default)
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "pdf_version": "v1",
    "message": "Can you explain what a JOIN is?"
  }'
```

### 4. Chat - Editor Mode (Explicit)
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "pdf_version": "v1",
    "message": "Add more examples about INNER JOIN. create update to pdf"
  }'
```

Response includes new PDF version:
```json
{
  "message_id": "msg_002",
  "content": "I've added 3 examples of INNER JOIN...",
  "mode": "editor",
  "new_pdf_version": "v2"
}
```

---

## Development Roadmap

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed phase breakdown.

### Current Status ✅
- Project skeleton with FastAPI backend
- Data models for jobs, PDFs, and chat
- API endpoints (implementation in progress)
- PDF generation prototype ([pdfmaker.py](pdfmaker.py))

### Next Steps 🚧
1. Refactor `pdfmaker.py` into modular services
2. Implement job management system
3. Integrate IBM watsonx.ai
4. Build chat system (tutor + editor modes)
5. Develop frontend UI

---

## Core Design Principles

### 1. Image Verification Before Explanation
Every image must be evaluated independently:
- Is this educational?
- What exactly is visible?
- Confidence score

Only high-confidence, relevant images are kept. This prevents hallucinated explanations.

### 2. Explicit PDF Edit Trigger
PDFs are **never modified implicitly**. Editor mode activates only with:

> "create update to pdf"

Without this phrase, the system operates in Tutor (Q&A) mode only.

### 3. Mandatory Versioning
- Every PDF has a version number (v1, v2, v3...)
- Older versions are never overwritten
- Chat context scoped to active PDF version

---

## Engineering Priorities

1. **Image Verification Accuracy** - Prevent hallucinations
2. **Explicit Edit Safety** - Never modify without trigger phrase  
3. **High-Quality PDFs** - Visual-first, well-structured
4. **Version Integrity** - 100% version preservation

*When trade-offs are required, prioritize correctness over speed.*

---

## Configuration

Key settings in `.env`:

```bash
# IBM watsonx.ai
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id

# Processing
MAX_VIDEO_SIZE_MB=500
CONFIDENCE_THRESHOLD=75
PDF_MAX_IMAGES=12

# Server
HOST=0.0.0.0
PORT=8000
```

---

## Testing

```bash
cd backend
pytest tests/
```

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details

---

## Support

- **Issues**: [GitHub Issues](https://github.com/zihan001/vid2note/issues)
- **Documentation**: [PROJECT_PLAN.md](PROJECT_PLAN.md)

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com)
- Powered by [IBM watsonx.ai](https://www.ibm.com/watsonx)
- Video processing with [ffmpeg](https://ffmpeg.org)

---
