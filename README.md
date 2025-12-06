# Codio - Interactive Learning Platform

<div align="center">
  <h3>🎓 Learn Coding by Doing</h3>
  <p>Integrate YouTube tutorials with live Python coding practice</p>
</div>

---

## 📋 Overview

**Codio** is an innovative educational platform that revolutionizes how students learn programming by combining video tutorials with real-time code execution. Built as a Final Year Project, it enables learners to pause YouTube videos, extract code from frames using AI, and practice immediately in an integrated Python compiler.

### 🎯 Key Features

- **🎬 YouTube Integration**: Load entire playlists or individual videos directly in the platform
- **⏸️ Pause-to-Code Mode**: Pause any video and automatically extract visible code using Google Gemini Vision AI
- **💻 Live Python Compiler**: Write and execute Python code instantly in the browser
- **📊 Progress Tracking**: Monitor your learning journey across multiple videos
- **🔄 Seamless Workflow**: Switch between video learning and coding practice effortlessly
- **🎨 Modern UI**: Built with Next.js 15, React 19, and Tailwind CSS

---

## 🏗️ Tech Stack

### Frontend
- **Framework**: Next.js 15.5.7 (App Router)
- **UI Library**: React 19.0.0
- **Language**: TypeScript 5.7.2
- **Styling**: Tailwind CSS 4.1.9
- **Components**: Radix UI, Lucide Icons
- **Notifications**: Sonner
- **Package Manager**: npm

### Backend
- **Framework**: Flask 3.1.0 (Python 3.14)
- **AI/ML**: Google Generative AI (Gemini 2.5 Flash)
- **Video Processing**: yt-dlp, OpenCV
- **CORS**: Flask-CORS 5.0.0
- **Server**: Gunicorn 23.0.0

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.14+
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/msaleh-12/Codio-Final-Year-Project.git
   cd Codio-Final-Year-Project
   ```

2. **Setup Backend**
   ```bash
   cd codio-backend
   python3 -m venv ../.venv
   source ../.venv/bin/activate  # On Windows: ..\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   
   Edit `codio-backend/pause_to_code_service.py` and add your Gemini API key:
   ```python
   GEMINI_API_KEY = "your-api-key-here"  # Line 29
   ```

4. **Setup Frontend**
   ```bash
   cd codio-frontend
   npm install
   ```

### Running the Application

1. **Start Backend Server** (Terminal 1)
   ```bash
   cd codio-backend
   source ../.venv/bin/activate
   python pause_to_code_api.py
   ```
   Backend runs on: `http://localhost:8080`

2. **Start Frontend Server** (Terminal 2)
   ```bash
   cd codio-frontend
   npm run dev
   ```
   Frontend runs on: `http://localhost:3000`

3. **Access the Application**
   
   Open your browser and navigate to `http://localhost:3000`

---

## 🎮 Usage

### Basic Workflow

1. **Login**: Use demo credentials
   - Email: `student@codio.com`
   - Password: `password123`

2. **Add Playlist**: Paste a YouTube playlist URL or single video URL

3. **Watch & Learn**: Video plays with native YouTube controls

4. **Pause to Code**: 
   - Pause the video when code appears on screen
   - System automatically extracts code using AI (3-5 seconds)
   - Code appears in integrated Python compiler

5. **Practice**: Edit and run the code, then return to video at the same timestamp

---

## 🏛️ Architecture

### System Flow

```
User → Frontend (Next.js) → Backend API (Flask) → YouTube + Gemini AI
                                ↓
                          Video Cache + Frame Extraction
                                ↓
                          Code Analysis & Return
```

### Key Components

**Frontend (`codio-frontend/`)**
- `app/`: Next.js App Router pages
- `components/`: Reusable React components
  - `auth/`: Authentication UI
  - `dashboard/`: Main dashboard and playlist management
  - `learning/`: Video player, compiler, progress tracking
- `lib/`: API client and utilities

**Backend (`codio-backend/`)**
- `pause_to_code_api.py`: Flask REST API (12 endpoints)
- `pause_to_code_service.py`: Core business logic
  - Video download and caching
  - Frame extraction at specific timestamps
  - Gemini Vision AI integration for code extraction
- `requirements.txt`: Python dependencies

---

## 🔐 Security

- ✅ **React2Shell CVE-2025-66478**: Patched (Next.js 15.5.7)
- ✅ **Zero vulnerabilities**: All dependencies regularly updated
- ✅ **CORS configured**: Secure cross-origin requests
- ✅ **API validation**: Input sanitization and error handling

---

## 🛠️ API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/playlist/videos` | Extract playlist videos |
| POST | `/api/v1/video/process` | Download video (lazy loading) |
| GET | `/api/v1/video/{id}/status` | Check processing status |
| GET | `/api/v1/video/{id}/frame?timestamp=X` | Extract code from frame |
| POST | `/api/v1/video/{id}/cancel` | Cancel processing |

See backend README for full API documentation.

---

## 📊 Features Status

- ✅ YouTube playlist/video integration
- ✅ Real-time video download with progress tracking
- ✅ Smart caching (videos persist across sessions)
- ✅ On-demand frame extraction
- ✅ AI-powered code extraction (Gemini Vision)
- ✅ Python compiler with syntax highlighting
- ✅ Resume video from paused position
- ✅ Progress sidebar with video list
- ⏳ User authentication (demo mode)
- ⏳ Multiple programming languages support
- ⏳ Code history and snippets library
- ⏳ Learning analytics dashboard

---

## 🤝 Contributing

This is a Final Year Project and contributions are welcome for educational purposes.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is developed as part of academic coursework. All rights reserved.

---

## 👨‍💻 Author

**Muhammad Saleh**
- Final Year Computer Science Student
- GitHub: [@msaleh-12](https://github.com/msaleh-12)

---

## 🙏 Acknowledgments

- **Google Gemini AI**: For powerful vision capabilities
- **YouTube**: For educational content platform
- **Vercel**: For Next.js framework and deployment platform
- **Flask**: For lightweight backend framework
- **Academic Supervisors**: For guidance and support

---

## 📧 Contact

For questions or feedback about this project, please open an issue on GitHub.

---

<div align="center">
  <p>Made with ❤️ for learners everywhere</p>
  <p>⭐ Star this repo if you find it helpful!</p>
</div>
