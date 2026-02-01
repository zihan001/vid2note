# Vid2Note - Project Plan & Task Breakdown

## Project Overview

**Vid2Note** is an AI-powered system that converts educational videos into high-quality, visual-first study PDFs with an interactive chat system for tutoring and document editing.

### Core Principles
- Visual understanding is mandatory
- Image ↔ explanation alignment must be verified
- PDF edits are explicit and versioned
- Tutor mode and editor mode are strictly separated

---

## Current Status

✅ **Completed:**
- Core PDF generation prototype (`pdfmaker.py`)
- Frame extraction & filtering
- Image verification with confidence scoring
- Annotation system (arrows, labels)
- Fallback visual diagrams
- Rate-limit handling

🔄 **Next Priority:**
- Backend API infrastructure
- Job management system
- Chat system implementation

---

## Phase Breakdown

### **Phase 1: Project Setup & Infrastructure**
**Status:** Not Started  
**Priority:** High

**Tasks:**
- [ ] Set up FastAPI backend structure
- [ ] Create directory structure for organized file storage
- [ ] Configure environment variables and secrets management
- [ ] Set up logging and monitoring framework
- [ ] Initialize database for metadata storage
- [ ] Configure CORS and security settings
- [ ] Set up development and production environments

**Deliverables:**
- Working FastAPI skeleton
- Database schema design
- Environment configuration files
- Basic health check endpoint

---

### **Phase 2: Video Processing Pipeline**
**Status:** Partially Complete (pdfmaker.py has basic implementation)  
**Priority:** High

**Tasks:**
- [ ] Refactor existing frame extraction code into modular service
- [ ] Implement ffmpeg integration for uniform sampling
- [ ] Add scene detection for intelligent frame selection
- [ ] Build timestamp tracking system
- [ ] Create pre-filtering pipeline:
  - [ ] Duplicate detection
  - [ ] Low-quality frame removal
  - [ ] Near-black frame filtering
- [ ] Add progress tracking for long videos
- [ ] Optimize for different video formats and resolutions

**Deliverables:**
- VideoProcessingService class
- Frame extraction API endpoint
- Quality metrics for filtered frames

---

### **Phase 3: Image Verification System**
**Status:** Partially Complete (pdfmaker.py has basic implementation)  
**Priority:** Critical

**Tasks:**
- [ ] Refactor image verification into standalone service
- [ ] Integrate IBM watsonx.ai API
- [ ] Implement structured verification prompt:
  - [ ] Educational relevance check
  - [ ] Visibility description
  - [ ] Confidence scoring (0-100)
- [ ] Build rejection logic for low-confidence frames
- [ ] Add batch verification for efficiency
- [ ] Implement auto-adaptation when too many frames rejected
- [ ] Create verification result caching

**Deliverables:**
- ImageVerificationService class
- Verification result schema
- Confidence threshold configuration
- Fallback strategies for low-quality videos

---

### **Phase 4: Content Generation**
**Status:** Partially Complete (pdfmaker.py has basic implementation)  
**Priority:** High

**Tasks:**
- [ ] Build explanation generator grounded in verified images
- [ ] Create example generator (1-2 per concept)
- [ ] Implement annotation instruction generator:
  - [ ] Arrow placement
  - [ ] Label text and positioning
  - [ ] Highlight regions
- [ ] Add content validation to prevent hallucinations
- [ ] Build structured output parser for LLM responses
- [ ] Optimize prompts for educational content quality

**Deliverables:**
- ContentGenerationService class
- Prompt templates for different content types
- Structured annotation schema
- Content quality metrics

---

### **Phase 5: Image Annotation Module**
**Status:** Partially Complete (pdfmaker.py has basic implementation)  
**Priority:** Medium

**Tasks:**
- [ ] Refactor annotation code into modular service
- [ ] Implement PIL/OpenCV annotation pipeline
- [ ] Build annotation instruction parser
- [ ] Support multiple annotation types:
  - [ ] Arrows (various styles)
  - [ ] Labels with backgrounds
  - [ ] Highlight boxes
  - [ ] Circles/underlines
- [ ] Add font management and text rendering
- [ ] Optimize for high-resolution images
- [ ] Create annotation preview generation

**Deliverables:**
- ImageAnnotationService class
- Annotation rendering engine
- Sample annotated outputs

---

### **Phase 6: PDF Generation Service**
**Status:** Partially Complete (pdfmaker.py has basic implementation)  
**Priority:** High

**Tasks:**
- [ ] Refactor PDF generation into modular service
- [ ] Design structured PDF sections:
  - [ ] Title page with metadata
  - [ ] Table of contents
  - [ ] Overview section (max 10 bullet points)
  - [ ] Concept cards (max 10)
  - [ ] Chapters with images (max 8)
  - [ ] Examples section (max 4)
  - [ ] Practice questions (max 10)
- [ ] Implement image-explanation pairing
- [ ] Add page numbering and navigation
- [ ] Embed version metadata
- [ ] Support custom styling/branding
- [ ] Optimize PDF file size

**Deliverables:**
- PDFGenerationService class
- PDF template system
- Version 1 PDF output
- PDF quality benchmarks

---

### **Phase 7: Versioning & Storage System**
**Status:** Not Started  
**Priority:** Critical

**Tasks:**
- [ ] Design version control schema
- [ ] Implement version numbering (v1, v2, v3...)
- [ ] Build storage system that preserves all versions
- [ ] Create version metadata tracking:
  - [ ] Generation timestamp
  - [ ] User who requested changes
  - [ ] Change description
  - [ ] Parent version reference
- [ ] Implement version retrieval API
- [ ] Add version comparison functionality
- [ ] Build version rollback capability
- [ ] Optimize storage for large PDFs

**Deliverables:**
- VersionControlService class
- Version metadata schema
- Storage strategy (filesystem or cloud)
- Version management API endpoints

---

### **Phase 8: Job Management System**
**Status:** Not Started  
**Priority:** High

**Tasks:**
- [ ] Design job state machine (UPLOADED → PROCESSING → COMPLETED/FAILED)
- [ ] Implement job ID generation
- [ ] Build job status tracking database
- [ ] Create progress tracking system:
  - [ ] Frame extraction progress
  - [ ] Verification progress
  - [ ] PDF generation progress
- [ ] Add error handling and recovery
- [ ] Implement job queue for concurrent processing
- [ ] Build job cancellation capability
- [ ] Add job result storage and cleanup

**Deliverables:**
- JobManagementService class
- Job status API endpoints
- WebSocket for real-time progress updates
- Job cleanup scheduler

---

### **Phase 9: Chat System - Tutor Mode**
**Status:** Not Started  
**Priority:** High

**Tasks:**
- [ ] Design chat context management
- [ ] Implement PDF content retrieval system:
  - [ ] Semantic search over PDF sections
  - [ ] Relevant image retrieval
  - [ ] Context ranking
- [ ] Build Q&A system using IBM watsonx.ai
- [ ] Implement scoped knowledge boundaries:
  - [ ] PDF content as primary source
  - [ ] External knowledge only for clarification
- [ ] Add off-topic question rejection
- [ ] Build conversation history management
- [ ] Create citation system (reference PDF sections)
- [ ] Implement response streaming

**Deliverables:**
- TutorService class
- Content retrieval system
- Chat API endpoints
- Prompt templates for tutor mode

---

### **Phase 10: Chat System - Editor Mode**
**Status:** Not Started  
**Priority:** Medium

**Tasks:**
- [ ] Implement explicit edit trigger detection:
  - [ ] Exact phrase matching: "create update to pdf"
  - [ ] Confirmation prompts
- [ ] Build edit instruction parser:
  - [ ] Add examples
  - [ ] Expand explanations
  - [ ] Add new sections/pages
  - [ ] Modify existing content
- [ ] Create edit validation system
- [ ] Implement incremental PDF regeneration
- [ ] Add edit preview before applying
- [ ] Build conflict resolution for version management
- [ ] Create edit history tracking

**Deliverables:**
- EditorService class
- Edit instruction schema
- PDF update pipeline
- Edit confirmation UI flow

---

### **Phase 11: Frontend - Upload & Processing UI**
**Status:** Not Started  
**Priority:** High

**Tasks:**
- [ ] Design and implement upload screen:
  - [ ] Video file upload (drag & drop)
  - [ ] Transcript file upload
  - [ ] File validation (format, size)
- [ ] Build processing status screen:
  - [ ] Real-time progress indicators
  - [ ] Stage-by-stage status display
  - [ ] Estimated time remaining
- [ ] Add error display and recovery options
- [ ] Implement file preview before upload
- [ ] Add upload cancellation
- [ ] Create responsive design for mobile

**Deliverables:**
- React/Vue components for upload
- Processing status UI
- Error handling UX
- File validation logic

---

### **Phase 12: Frontend - PDF Viewer & Chat**
**Status:** Not Started  
**Priority:** High

**Tasks:**
- [ ] Implement PDF viewer component:
  - [ ] Embedded PDF rendering
  - [ ] Zoom and navigation controls
  - [ ] Page thumbnails
  - [ ] Annotation highlighting
- [ ] Build chat interface:
  - [ ] Message input/display
  - [ ] Mode indicator (Tutor/Editor)
  - [ ] Citation links to PDF sections
  - [ ] Response streaming
- [ ] Create version selector:
  - [ ] Version dropdown/timeline
  - [ ] Version comparison view
  - [ ] Rollback functionality
- [ ] Add download PDF functionality
- [ ] Implement responsive layout

**Deliverables:**
- PDF viewer component
- Chat UI component
- Version management UI
- Complete user flow

---

### **Phase 13: API Integration & Testing**
**Status:** Not Started  
**Priority:** High

**Tasks:**
- [ ] Connect frontend to all backend endpoints
- [ ] Implement comprehensive error handling:
  - [ ] Network errors
  - [ ] API rate limits
  - [ ] Timeout handling
- [ ] Add retry logic for LLM calls
- [ ] Build rate limiting middleware
- [ ] Implement API authentication/authorization
- [ ] Create end-to-end tests:
  - [ ] Upload → PDF generation
  - [ ] Chat interactions
  - [ ] Version management
- [ ] Add integration tests for all services
- [ ] Perform load testing

**Deliverables:**
- Complete API integration
- Test suite (unit, integration, e2e)
- Performance benchmarks
- API documentation

---

### **Phase 14: Quality Assurance & Optimization**
**Status:** Not Started  
**Priority:** Medium

**Tasks:**
- [ ] Test image verification accuracy:
  - [ ] Educational relevance precision
  - [ ] False positive/negative rates
  - [ ] Confidence calibration
- [ ] Validate edit safety mechanisms:
  - [ ] Explicit trigger enforcement
  - [ ] Version integrity checks
  - [ ] Rollback safety
- [ ] Optimize PDF generation quality:
  - [ ] Image resolution optimization
  - [ ] Layout improvements
  - [ ] Content organization
- [ ] Test version integrity under concurrent edits
- [ ] Implement fallback mechanisms for failures
- [ ] Optimize LLM token usage
- [ ] Improve processing speed
- [ ] Add caching strategies

**Deliverables:**
- QA test results
- Performance optimization report
- Quality metrics dashboard
- Updated documentation

---

### **Phase 15: Deployment & Documentation**
**Status:** Not Started  
**Priority:** Medium

**Tasks:**
- [ ] Set up production server infrastructure
- [ ] Configure file storage (local or cloud)
- [ ] Set up production database
- [ ] Implement monitoring and alerting:
  - [ ] Error tracking (Sentry)
  - [ ] Performance monitoring
  - [ ] Usage analytics
- [ ] Create user documentation:
  - [ ] Getting started guide
  - [ ] Feature documentation
  - [ ] FAQ
- [ ] Write API documentation (OpenAPI/Swagger)
- [ ] Create developer setup guide
- [ ] Implement backup and disaster recovery
- [ ] Set up CI/CD pipeline

**Deliverables:**
- Production deployment
- Monitoring dashboard
- Complete documentation
- Deployment scripts

---

## Engineering Priorities

In order of importance:

1. **Image Verification Accuracy** - Must prevent hallucinations
2. **Explicit Edit Safety** - PDF never modified without exact trigger phrase
3. **High-Quality PDFs** - Visual-first, well-structured, educational
4. **Version Integrity** - All versions preserved, never overwritten

## Success Metrics

- **Image Verification**: >90% precision on educational relevance
- **Edit Safety**: 0% unintended PDF modifications
- **PDF Quality**: User satisfaction score >4.5/5
- **Version Integrity**: 100% version preservation
- **Processing Speed**: <5 minutes for 30-minute video
- **Chat Response Time**: <3 seconds for tutor mode

---

## Risk Management

### Technical Risks
- **LLM Rate Limits**: Mitigated by retry logic and request batching
- **Video Processing Failures**: Fallback to more frame candidates
- **Poor Image Quality**: Fallback visual diagrams if <4 good frames
- **Version Conflicts**: Explicit edit mode prevents conflicts

### Product Risks
- **Hallucinated Content**: Prevented by mandatory image verification
- **Accidental PDF Edits**: Prevented by explicit "create update to pdf" trigger
- **Version Confusion**: Clear version UI with timestamps

---

## Next Steps

**Immediate Priorities** (Week 1-2):
1. Set up FastAPI backend infrastructure
2. Refactor pdfmaker.py into modular services
3. Implement job management system
4. Build basic API endpoints

**Short-term Goals** (Month 1):
1. Complete backend pipeline (Phases 1-8)
2. Integrate IBM watsonx.ai properly
3. Implement versioning system
4. Build chat tutor mode

**Medium-term Goals** (Month 2-3):
1. Develop frontend UI
2. Implement editor mode
3. Complete end-to-end testing
4. Deploy MVP

---

## Notes

- **Current Code Status**: `pdfmaker.py` provides solid foundation for Phases 2-6
- **Architecture Decision**: Prioritize correctness over speed
- **LLM Choice**: IBM watsonx.ai as specified in requirements
- **No Compromises**: Image verification and edit safety are non-negotiable
