# Testing Guide - Transcript Search & Concept Detection

This guide provides multiple ways to test the new features.

## 🧪 Testing Methods

### Method 1: Python Test Script (Recommended)

**Comprehensive Test:**
```bash
cd codio-backend
python test_new_features.py <video_id> [search_query]
```

**Example:**
```bash
# Test with a video ID
python test_new_features.py dQw4w9WgXcQ

# Test with specific search query
python test_new_features.py dQw4w9WgXcQ loops
```

**What it tests:**
- ✅ Backend health check
- ✅ Video processing status
- ✅ Transcript search functionality
- ✅ Get detected concepts
- ✅ Detect concepts (AI analysis)

---

### Method 2: Quick API Testing

**Simple endpoint test:**
```bash
cd codio-backend
python test_api_quick.py <endpoint> [method] [json_data]
```

**Examples:**
```bash
# Health check
python test_api_quick.py /health

# Search transcript
python test_api_quick.py "/video/dQw4w9WgXcQ/transcript/search?query=python"

# Get concepts
python test_api_quick.py /video/dQw4w9WgXcQ/concepts

# Detect concepts
python test_api_quick.py /video/dQw4w9WgXcQ/concepts/detect POST
```

---

### Method 3: cURL Commands

**Health Check:**
```bash
curl http://localhost:8080/health
```

**Transcript Search:**
```bash
# Search for "loops" in transcript
curl "http://localhost:8080/api/v1/video/dQw4w9WgXcQ/transcript/search?query=loops"

# Case-sensitive search
curl "http://localhost:8080/api/v1/video/dQw4w9WgXcQ/transcript/search?query=Python&case_sensitive=true"
```

**Get Detected Concepts:**
```bash
curl http://localhost:8080/api/v1/video/dQw4w9WgXcQ/concepts
```

**Detect Concepts (AI Analysis):**
```bash
curl -X POST http://localhost:8080/api/v1/video/dQw4w9WgXcQ/concepts/detect
```

**Video Status:**
```bash
curl http://localhost:8080/api/v1/video/dQw4w9WgXcQ/status
```

---

### Method 4: Postman/Thunder Client

**Import these requests:**

1. **Transcript Search**
   - Method: `GET`
   - URL: `http://localhost:8080/api/v1/video/{video_id}/transcript/search`
   - Query Params:
     - `query`: `loops` (required)
     - `case_sensitive`: `false` (optional)

2. **Get Concepts**
   - Method: `GET`
   - URL: `http://localhost:8080/api/v1/video/{video_id}/concepts`

3. **Detect Concepts**
   - Method: `POST`
   - URL: `http://localhost:8080/api/v1/video/{video_id}/concepts/detect`

---

### Method 5: Browser Testing (Frontend)

1. **Open the app:** http://localhost:3000
2. **Login/Signup** with your credentials
3. **Add a playlist** or video URL
4. **Open learning view** for a video
5. **Test Transcript Search:**
   - Click "Search" tab in right sidebar
   - Type keywords (e.g., "loops", "function", "array")
   - Click "Search"
   - Click any result to jump to timestamp
6. **Test Concept Detection:**
   - Click "Concepts" tab
   - Click "Detect Concepts" button
   - Wait 10-30 seconds for AI analysis
   - View detected concepts with timestamps
   - Click timestamps to jump to video

---

### Method 6: Python Interactive Testing

```python
# Start Python REPL
python

# Import and test
from pause_to_code_service import PauseToCodeService

service = PauseToCodeService()

# Test transcript search
video_id = "dQw4w9WgXcQ"
matches = service.search_transcript(video_id, "python")
print(f"Found {len(matches)} matches")
for match in matches[:3]:
    print(f"  {match['timestamp']}s: {match['text'][:50]}...")

# Test concept detection
concepts = service.detect_and_store_concepts(video_id)
print(f"Detected {len(concepts)} concepts")
for concept in concepts:
    print(f"  {concept.concept_name} ({concept.category})")

# Get concepts
concepts = service.get_detected_concepts(video_id)
print(f"Found {len(concepts)} concepts")
```

---

## 📋 Test Checklist

### Transcript Search
- [ ] Search returns results for existing keywords
- [ ] Search handles empty results gracefully
- [ ] Case-sensitive option works
- [ ] Timestamps are accurate
- [ ] Clicking results jumps to correct video time

### Concept Detection
- [ ] Concepts are detected correctly
- [ ] Categories are assigned properly
- [ ] Confidence scores are reasonable (0.0-1.0)
- [ ] Timestamps link to correct video moments
- [ ] Multiple concepts can be detected
- [ ] Detection can be re-run (updates cache)

### Integration
- [ ] Both features work together
- [ ] No conflicts with existing features
- [ ] UI is responsive and user-friendly
- [ ] Error handling works correctly

---

## 🐛 Troubleshooting

**"No transcript available"**
- Video may not have captions/subtitles
- Check if video has auto-generated captions
- Some videos don't have transcripts

**"No concepts detected"**
- Video must be processed first (status='completed')
- Transcript must be available
- Try running detection again

**"Video not found"**
- Process the video first via `/api/v1/video/process`
- Check video ID is correct
- Wait for processing to complete

**API errors**
- Check backend server is running (port 8080)
- Check `.env` file has correct API keys
- Check server logs for errors

---

## 📊 Expected Results

### Transcript Search
```json
{
  "success": true,
  "video_id": "dQw4w9WgXcQ",
  "query": "python",
  "matches_count": 5,
  "matches": [
    {
      "timestamp": 45.5,
      "text": "In Python, we can use loops...",
      "duration": 3.2,
      "match_start": 3,
      "match_length": 6
    }
  ]
}
```

### Concept Detection
```json
{
  "success": true,
  "video_id": "dQw4w9WgXcQ",
  "concepts_count": 3,
  "concepts": [
    {
      "concept_name": "loops",
      "category": "control_flow",
      "timestamps": [45.5, 120.3],
      "confidence": 0.95,
      "description": "Teaching for loops and while loops"
    }
  ]
}
```

---

## 🚀 Quick Start Testing

1. **Start servers:**
   ```bash
   # Backend (Terminal 1)
   cd codio-backend
   python pause_to_code_api.py
   
   # Frontend (Terminal 2)
   cd codio-frontend
   npm run dev
   ```

2. **Process a video** (via frontend or API)

3. **Run test script:**
   ```bash
   python test_new_features.py <video_id>
   ```

4. **Or test in browser:** http://localhost:3000

---

Happy Testing! 🎉


