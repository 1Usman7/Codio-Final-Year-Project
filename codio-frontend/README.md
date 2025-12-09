# Codio - Interactive Learning Platform with Pause-to-Code

An AI-powered interactive learning platform that allows you to watch YouTube tutorials and extract code in real-time with pause-to-code functionality.

## Features

- **AI Code Extraction** - Gemini 2.0 Flash analyzes video frames for code detection  
- **YouTube Integration** - Process any Python tutorial playlist or single video  
- **In-Browser Python Compiler** - Run and test extracted code instantly  
- **JWT Authentication** - Secure user authentication with access and refresh tokens  
- **Progress Tracking** - SQLite database stores playlist progress and watch history  
- **Playlist Management** - Save and resume multiple playlists  
- **Smart Detection** - AI distinguishes code from explanations with confidence scores  
- **Video Progress** - Track completion percentage for each video and playlist  

## Tech Stack

**Frontend**:
- Next.js 15.5.7
- React 19.0.0
- TypeScript 5.7.2
- TailwindCSS
- Shadcn UI Components

**Backend**:
- Flask 3.1.0
- Python 3.14.0
- SQLite Database
- JWT Authentication (PyJWT)
- OpenCV for video processing
- yt-dlp for YouTube downloads

**AI**:
- Google Gemini 2.0 Flash (Vision Language Model)

## Quick Start

### Prerequisites
- **Python 3.14+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **npm** (comes with Node.js)
- **ffmpeg** (for video processing)
  - macOS: `brew install ffmpeg`
  - Windows: `winget install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 1. Backend Setup
```bash
cd codio-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python pause_to_code_api.py
```
Backend runs on: http://localhost:8080

### 2. Frontend Setup
```bash
cd codio-frontend
npm install
npm run dev
```
Frontend runs on: http://localhost:3000

### 3. Environment Variables
Create `.env` file in backend directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 4. Use the App
1. Open http://localhost:3000
2. Sign up with email and password
3. Login with your credentials
4. Paste a YouTube Python tutorial URL or playlist
5. Wait for video processing (1-2 minutes for first video)
6. Watch the video and pause to extract code!
7. Test extracted code in the built-in Python compiler

## Implementation Status

### Completed Features

**Authentication & Security**:
- JWT-based authentication system
- Access tokens (60 min) and refresh tokens (7 days)
- Secure password hashing with bcrypt
- Protected API endpoints
- Auto token refresh on expiry

**Database**:
- SQLite database for data persistence
- User management (registration, login)
- Playlist tracking with progress
- Video progress tracking (watch time, completion status)
- Recent playlists display

**UI/UX**:
- Modern, responsive design with dark mode
- Playlist input and management
- Video player with pause-to-code
- Built-in Python compiler with real-time execution
- Progress sidebar showing video completion
- Recent playlists section with progress indicators

**Backend API**:
- YouTube playlist/video extraction
- Video processing and analysis
- Code extraction at specific timestamps
- Processing status tracking with real-time progress
- User playlist management
- Progress saving and retrieval

**Video Processing**:
- Automatic video download from YouTube
- Frame extraction and analysis
- Code detection using AI
- Caching system for processed videos
- Background processing with status updates

### Technical Details

**API Endpoints**:
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/playlist/videos` - Get playlist videos with title
- `POST /api/v1/video/process` - Process video for code extraction
- `GET /api/v1/video/<id>/status` - Get processing status
- `GET /api/v1/video/<id>/code?timestamp=<sec>` - Extract code at timestamp
- `POST /api/v1/user/playlist` - Save user playlist
- `GET /api/v1/user/<email>/playlists` - Get user's playlists
- `POST /api/v1/user/progress` - Save video progress
- `GET /api/v1/user/<email>/playlist/<id>/progress` - Get playlist progress
- `DELETE /api/v1/user/<email>/playlist/<id>` - Delete playlist

**Database Schema**:
- `users` - User accounts (email, name, password hash)
- `user_playlists` - Saved playlists with metadata
- `video_progress` - Individual video watch progress

## Documentation

- [SETUP.md](./SETUP.md) - Detailed setup instructions
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide

## Troubleshooting

**Backend won't start**: 
- Check Python version: `python --version` (should be 3.14+)
- Activate virtual environment
- Install requirements: `pip install -r requirements.txt`

**Frontend won't start**:
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and `.next`, then run `npm install`

**ffmpeg error**: 
- Install ffmpeg: `brew install ffmpeg` (macOS) or `winget install ffmpeg` (Windows)

**Port already in use**:
- Backend: Kill process on port 8080: `lsof -ti:8080 | xargs kill -9`
- Frontend: Kill process on port 3000: `lsof -ti:3000 | xargs kill -9`

**Login/Signup issues**:
- Check JWT environment variables are set
- Clear browser localStorage
- Check backend logs for errors

## Testing

Backend includes comprehensive test suite:
- 18 API endpoint tests
- 12 database operation tests
- JWT authentication tests
- All tests passing

Run tests:
```bash
cd codio-backend
pytest test_pause_to_code.py -v
```

## License

MIT
