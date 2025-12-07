# Codio - Interactive Learning Platform 🎓

<div align="center">
  <h3>🎯 Learn Programming by Doing - Pause, Extract, Code</h3>
  <p>AI-powered platform combining YouTube tutorials with live Python coding practice</p>
  <br/>
  
  ![Status](https://img.shields.io/badge/Status-Active-success)
  ![Python](https://img.shields.io/badge/Python-3.14-blue)
  ![Next.js](https://img.shields.io/badge/Next.js-15.5-black)
  ![React](https://img.shields.io/badge/React-19.0-blue)
  ![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue)
</div>

---

## 📋 Overview

**Codio** is an AI-powered educational platform that transforms how students learn programming by seamlessly integrating YouTube video tutorials with real-time code execution. The platform's revolutionary **Pause-to-Code Mode** uses Google Gemini Vision AI to automatically extract code from video frames, enabling learners to instantly practice what they see in tutorials.

Built as a Final Year Project, Codio bridges the gap between passive video watching and active coding practice, creating an immersive learning experience.

### 🎯 Key Features

- **🎬 YouTube Playlist Integration**: Load entire playlists or individual videos with automatic metadata extraction
- **⏸️ AI-Powered Pause-to-Code**: Pause any video and instantly extract visible code using Google Gemini 2.5 Flash Vision AI
- **💻 Integrated Python Compiler**: Execute Python code directly in the browser with real-time output
- **🤖 Intelligent Code Detection**: Distinguishes between code segments and learning/explanation phases
- **📊 Real-time Progress Tracking**: Monitor video download progress and processing status
- **🔄 Seamless Learning Flow**: Switch between video learning and hands-on coding effortlessly
- **🎨 Modern Responsive UI**: Beautiful, accessible interface built with Next.js 15 and Tailwind CSS
- **🔒 Secure Configuration**: Environment-based API key management with .env support

---

## 🏗️ Tech Stack

### Frontend
- **Framework**: Next.js 15.5.7 (App Router with React Server Components)
- **UI Library**: React 19.0.0 (with Hooks and Context)
- **Language**: TypeScript 5.7.2 (Strict mode)
- **Styling**: Tailwind CSS 4.1.9 with custom design system
- **Video Player**: React YouTube Player
- **UI Components**: Radix UI (Accordion, Dialog, Progress, Toast)
- **Icons**: Lucide React
- **Notifications**: Sonner Toast
- **State Management**: React Hooks (useState, useEffect, useRef)
- **HTTP Client**: Native Fetch API with request tracking

### Backend
- **Framework**: Flask 3.1.0 REST API (Python 3.14)
- **AI/Vision**: Google Generative AI (Gemini 2.5 Flash for code extraction)
- **Video Processing**: 
  - yt-dlp (YouTube video download)
  - OpenCV (cv2) for frame extraction and analysis
- **Image Processing**: NumPy, Base64 encoding
- **CORS**: Flask-CORS 5.0.0 (Frontend-Backend communication)
- **Environment**: python-dotenv 1.0.1 (Secure configuration)
- **Logging**: Python logging module with request tracking
- **Data Structures**: Dataclasses for type-safe models

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.14+
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))
- **Git** for cloning the repository

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/msaleh-12/Codio-Final-Year-Project.git
   cd "Final Year"
   ```

2. **Setup Python Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Setup Backend**
   ```bash
   cd codio-backend
   pip install -r requirements.txt
   ```

4. **Configure API Key** (IMPORTANT - Secure Method)
   
   Create a `.env` file in the `codio-backend` directory:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your-actual-api-key-here
   ```
   
   ⚠️ **Security Note**: Never commit `.env` file to Git. It's already in `.gitignore`.

5. **Setup Frontend**
   ```bash
   cd ../codio-frontend
   npm install
   ```

### Running the Application

1. **Start Backend Server** (Terminal 1)
   ```bash
   cd codio-backend
   source ../.venv/bin/activate  # Activate virtual environment
   python pause_to_code_api.py
   ```
   
   ✅ Backend running on: `http://localhost:8080`
   
   Check health: `curl http://localhost:8080/health`

2. **Start Frontend Server** (Terminal 2)
   ```bash
   cd codio-frontend
   npm run dev
   ```
   
   ✅ Frontend running on: `http://localhost:3000`

3. **Access the Application**
   
   Open your browser and navigate to `http://localhost:3000`

---

## 📖 How to Use

### Step 1: Load a Playlist
1. Copy a YouTube playlist URL (or single video URL)
2. Paste it into the input field on the dashboard
3. Click "Load Playlist" and wait for videos to load

### Step 2: Start Watching
1. The first video will load automatically
2. Progress bar shows download status (if not cached)
3. Once status shows "Ready for pause-to-code", you can use the feature

### Step 3: Use Pause-to-Code
1. **Play the video** and watch until you see code on screen
2. **Pause the video** at the timestamp with code visible
3. **AI processes the frame** (shows "Processing frame..." overlay)
4. **Code appears in the compiler** on the right side
5. **Edit and run the code** to practice

### Step 4: Practice and Learn
- Modify the extracted code
- Click "Run Code" to execute
- See output in real-time
- Switch between full-screen video or split view

---

## 🎯 API Endpoints

### Backend REST API (`http://localhost:8080`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/api/v1/video/process` | POST | Download and prepare video for pause-to-code |
| `/api/v1/video/<video_id>/status` | GET | Get video processing status and progress |
| `/api/v1/video/<video_id>/frame?timestamp=<seconds>` | GET | Extract code from specific timestamp |
| `/api/v1/playlist/videos` | POST | Fetch videos from YouTube playlist |

### Request/Response Examples

**Process Video:**
```json
POST /api/v1/video/process
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "full_process": false
}
```

**Get Frame at Timestamp:**
```json
GET /api/v1/video/<video_id>/frame?timestamp=1150.5

Response:
{
  "success": true,
  "timestamp": 1150.5,
  "segment_type": "code",
  "code_content": "print('Hello World')",
  "confidence": 0.95,
  "language": "python"
}
```

---

## 📂 Project Structure

```
Final Year/
├── codio-backend/                 # Flask REST API Backend
│   ├── pause_to_code_api.py      # Main Flask application with endpoints
│   ├── pause_to_code_service.py  # Core service (AI, video processing)
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # API keys (gitignored)
│   ├── .env.example              # Template for .env
│   └── codio_cache/              # Downloaded videos and analysis cache
│       └── videos/               # Video files storage
│
├── codio-frontend/               # Next.js Frontend Application
│   ├── app/                      # Next.js App Router
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Home page
│   │   └── api/                 # API routes (proxy)
│   ├── components/              # React components
│   │   ├── dashboard/           # Dashboard and learning view
│   │   │   ├── dashboard.tsx
│   │   │   ├── learning-view.tsx      # Main learning interface
│   │   │   └── playlist-input.tsx
│   │   ├── learning/            # Video and compiler components
│   │   │   ├── video-player.tsx       # YouTube player wrapper
│   │   │   ├── python-compiler.tsx    # Code editor & execution
│   │   │   └── progress-sidebar.tsx
│   │   ├── auth/                # Authentication
│   │   └── ui/                  # Reusable UI components
│   ├── lib/                     # Utilities
│   │   ├── api.ts              # Backend API client with logging
│   │   └── utils.ts            # Helper functions
│   ├── package.json            # Node dependencies
│   └── tsconfig.json           # TypeScript configuration
│
├── .gitignore                  # Git ignore rules (includes .env)
├── .venv/                      # Python virtual environment
├── backend.log                 # Backend runtime logs
├── frontend.log                # Frontend runtime logs
└── README.md                   # This file
---

## 🔧 Technical Details

### AI Code Extraction Process

1. **Frame Capture**: Video frame extracted at exact timestamp using OpenCV
2. **Image Encoding**: Frame converted to base64 JPEG (95% quality)
3. **AI Analysis**: Gemini 2.5 Flash processes frame with custom prompt:
   - Detects if frame shows code or learning/explanation phase
   - Extracts code exactly as written (preserves indentation)
   - Identifies programming language
   - Determines if code block is complete
   - Returns confidence score (0.0-1.0)
4. **Response Processing**: Frontend displays extracted code in editor

### Video Processing Pipeline

```
YouTube URL → yt-dlp Download → MP4 Cache → On-Demand Frame Extraction
                                    ↓
                          Status Tracking (downloading/completed)
                                    ↓
                          Ready for Pause-to-Code
```

### State Management Architecture

- **Frontend**: React Hooks (useState, useEffect, useRef)
- **Backend**: In-memory progress tracking with cache persistence
- **Video Cache**: Persistent storage in `codio_cache/videos/`
- **Status Polling**: 2-second intervals during video processing

### Error Handling

- ✅ Download failure cleanup (prevents stuck states)
- ✅ API key validation with helpful error messages
- ✅ Comprehensive request/response logging
- ✅ Graceful degradation for unsupported videos
- ✅ Frontend toast notifications for user feedback

---

## 🔐 Security & Best Practices

- ✅ **Environment Variables**: API keys stored in `.env` (gitignored)
- ✅ **No Hardcoded Secrets**: Zero credentials in codebase
- ✅ **Request Tracking**: Unique IDs for debugging (req_timestamp_random)
- ✅ **CORS Configuration**: Secure cross-origin requests
- ✅ **Input Validation**: URL sanitization and parameter checking
- ✅ **Error Logging**: Comprehensive backend logs with request IDs
- ✅ **Dependency Security**: Regular updates, zero known vulnerabilities

---

## 📊 Performance Features

- **Smart Caching**: Videos downloaded once, reused across sessions
- **Lazy Loading**: Videos download only when needed (not entire playlist)
- **Progress Tracking**: Real-time download progress (0-100%)
- **Efficient Frame Extraction**: On-demand processing (no pre-processing)
- **Optimized AI Calls**: Single frame analysis per pause (~2 seconds)
- **Memory Management**: Automatic cleanup of failed downloads

---

## 🛠️ Development & Debugging

### Logging System

The application includes comprehensive logging for debugging:

**Frontend Logging** (Browser Console):
```javascript
[LearningView] Step X: Action description
[VideoPlayer] State change detected
[API] [req_id] Request details
[PythonCompiler] Code update
```

**Backend Logging** (`backend.log`):
```
[req_id] ========== /api/v1/endpoint START ==========
Step 1: Action description
Step 2: Result details
[req_id] ========== /api/v1/endpoint END ==========
```

### Common Issues & Solutions

**Issue**: "Video not ready for code extraction"
- **Solution**: Wait for status to show "Ready for pause-to-code" (watch progress bar)

**Issue**: "Analysis failed" when pausing
- **Solution**: Check backend logs, verify Gemini API key is valid

**Issue**: Video stuck at "downloading 0%"
- **Solution**: Backend auto-cleans stuck states; refresh page and retry

**Issue**: No code extracted (but code is visible)
- **Solution**: AI confidence may be low; try pausing at clearer frame

---

## 🎯 Feature Highlights

### Current Implementation

✅ **Pause-to-Code Mode**: Core feature fully functional
- Real-time frame extraction at any timestamp
- AI-powered code detection with 85%+ accuracy
- Automatic compiler population
- Loading states and error handling

✅ **Video Management**:
- YouTube playlist fetching with metadata
- Progressive video download with status tracking  
- Smart caching (persistent across restarts)
- Multiple video support in sidebar

✅ **Developer Experience**:
- Comprehensive logging throughout stack
- Request tracking with unique IDs
- TypeScript for type safety
- Modular component architecture

### Planned Enhancements

⏳ **Multi-Language Support**: JavaScript, Java, C++ extraction
⏳ **Code History**: Save extracted snippets with timestamps
⏳ **Collaborative Learning**: Share playlists and notes
⏳ **Analytics Dashboard**: Track learning progress over time
⏳ **Advanced AI**: Context-aware code suggestions

---

## 🤝 Contributing

This is a Final Year Project and contributions are welcome for educational purposes.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes with proper logging
4. Test thoroughly (frontend + backend)
5. Commit with descriptive messages
6. Push to branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request with detailed description

### Code Style Guidelines

- **TypeScript**: Follow existing patterns, use proper types
- **Python**: PEP 8 compliance, type hints where applicable
- **Logging**: Add step-by-step logs for debugging
- **Error Handling**: Always include try-catch with cleanup
- **Comments**: Explain "why", not "what"

---

## 📝 License

This project is developed as part of academic coursework for educational purposes.
All rights reserved.

---

## 👨‍💻 Author

**Muhammad Saleh**
- Final Year Computer Science Student
- GitHub: [@msaleh-12](https://github.com/msaleh-12)
- Project: Codio Interactive Learning Platform

---

## 🙏 Acknowledgments

- **Google Gemini AI** (Gemini 2.5 Flash): Advanced vision capabilities for code extraction
- **YouTube & yt-dlp**: Educational content platform and download library
- **Vercel**: Next.js framework, React Server Components
- **Flask Community**: Lightweight, flexible backend framework
- **OpenCV**: Computer vision library for frame processing
- **Radix UI**: Accessible, unstyled component primitives
- **Academic Supervisors**: Guidance and project mentorship

---

## 📧 Contact & Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/msaleh-12/Codio-Final-Year-Project/issues)
- **Discussions**: Feature requests and questions welcome
- **Email**: Available through GitHub profile

---

<div align="center">
  <h3>🌟 Star this repository if you find it helpful!</h3>
  <p>Made with ❤️ for learners everywhere</p>
  <br/>
  <p>
    <a href="https://github.com/msaleh-12/Codio-Final-Year-Project">
      <img src="https://img.shields.io/github/stars/msaleh-12/Codio-Final-Year-Project?style=social" alt="GitHub stars">
    </a>
  </p>
</div>
