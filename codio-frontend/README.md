# Codio - AI-Powered Code Extraction from YouTube

Extract code from Python tutorial videos using AI and practice in an in-browser compiler.

## Quick Start

### 1. Install Prerequisites
- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python 3.12** ([Download](https://www.python.org/downloads/))
- **ffmpeg** (`winget install ffmpeg` on Windows)

### 2. Start Backend
```bash
cd f-y-p-pause-to-code
pip install -r requirements.txt
python pause_to_code_api.py
```
Backend runs on: http://localhost:5000

### 3. Start Frontend
```bash
cd codio-frontend
npm install --legacy-peer-deps
npm run dev
```
Frontend runs on: http://localhost:3000

### 4. Use the App
1. Open http://localhost:3000
2. Login (any credentials)
3. Paste a YouTube Python tutorial URL
4. Wait for AI processing (1-2 minutes)
5. Pause video to extract code!

## Features

✨ **AI Code Extraction** - Gemini 2.5 Flash analyzes video frames  
🎥 **YouTube Integration** - Process any Python tutorial  
💻 **In-Browser Compiler** - Run Python code instantly  
🧠 **Smart Detection** - Distinguishes code from explanations  
📊 **Confidence Scores** - See AI accuracy  

## Documentation

- [SETUP.md](./SETUP.md) - Detailed setup instructions
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Sharing with others
- [API_README.md](../f-y-p-pause-to-code/API_README.md) - Backend API docs

## Tech Stack

**Frontend**: Next.js 15, React 19, TypeScript, TailwindCSS  
**Backend**: Flask, Python 3.12, OpenCV, yt-dlp  
**AI**: Google Gemini 2.5 Flash (Vision Language Model)

## Requirements

- Python 3.12 (NOT 3.14)
- Node.js 18+
- ffmpeg

## Troubleshooting

**Backend won't start**: Check Python version (`python --version`)  
**ffmpeg error**: Install ffmpeg  
**Port in use**: Change ports in config files  

## License

MIT
