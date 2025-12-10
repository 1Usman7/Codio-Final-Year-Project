#!/usr/bin/env python3
"""
Codio Pause-to-Code Backend Service
Complete implementation using Gemini 2.5 Pro API for VLM-based code extraction
"""

import os
import time
import json
import cv2
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
import yt_dlp
import numpy as np
from dataclasses import dataclass, asdict
import hashlib
from dotenv import load_dotenv
import requests
import re

# Load environment variables from .env file
load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Gemini API - Use environment variable for security
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    logger.error("CRITICAL: GEMINI_API_KEY environment variable not set!")
    logger.error("Please set it by running: export GEMINI_API_KEY='your-api-key'")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured successfully")


@dataclass
class CodeSegment:
    """Represents a code segment extracted from video"""
    timestamp: float
    frame_number: int
    segment_type: str  # 'code' or 'learning'
    code_content: Optional[str]
    learning_topic: Optional[str]
    confidence: float
    language: str
    code_complete: bool


@dataclass
class TranscriptEntry:
    """Represents a transcript entry with timestamp"""
    timestamp: float
    text: str
    duration: float  # Duration of this transcript segment


@dataclass
class DetectedConcept:
    """Represents a detected programming concept"""
    concept_name: str  # e.g., "loops", "arrays", "recursion"
    category: str  # e.g., "control_flow", "data_structures", "algorithms"
    timestamps: List[float]  # List of timestamps where this concept appears
    confidence: float  # Detection confidence (0.0-1.0)
    description: Optional[str]  # Brief description of the concept


@dataclass
class VideoAnalysis:
    """Complete video analysis result"""
    video_id: str
    video_title: str
    duration: float
    total_frames_analyzed: int
    code_segments: List[CodeSegment]
    metadata: Dict
    extraction_date: str
    transcript: Optional[List[TranscriptEntry]] = None  # Optional transcript entries
    detected_concepts: Optional[List[DetectedConcept]] = None  # Optional detected concepts


class GeminiCodeExtractor:
    """Core VLM-based code extraction using Gemini"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.generation_config = {
            "temperature": 0.1,  # Low temperature for consistent extraction
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
    def encode_frame(self, frame: np.ndarray) -> str:
        """Encode frame to base64 for Gemini API"""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return base64.b64encode(buffer).decode('utf-8')
    
    def analyze_frame(self, frame: np.ndarray, timestamp: float) -> Dict:
        """
        Analyze a single frame using Gemini VLM
        Returns structured data about code presence and content
        """
        try:
            # Prepare the prompt for detailed analysis
            prompt = """Analyze this video frame from a Python programming tutorial.

Your task:
1. Determine if this frame shows CODE being written/displayed or if it's a LEARNING/EXPLANATION phase
2. If code is visible, extract it EXACTLY as shown (preserve indentation, syntax)
3. If it's an explanation/learning phase, note what concept is being taught

Response format (JSON only, no markdown):
{
    "segment_type": "code|learning",
    "has_code": true/false,
    "code_content": "extracted code or null",
    "learning_topic": "topic being explained or null",
    "confidence": 0.0-1.0,
    "language": "python",
    "code_complete": true/false
}

Rules:
- Use "code" only when actual code is visible in an IDE/editor
- Use "learning" for slides, diagrams, explanations, or instructor speaking
- Extract code EXACTLY - preserve all spacing, indentation, comments
- Set code_complete to true only if it's a runnable snippet
- Be conservative: if unsure, classify as "learning"
"""

            # Convert frame to PIL Image format for Gemini
            import PIL.Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(frame_rgb)
            
            # Generate analysis
            response = self.model.generate_content(
                [prompt, pil_image],
                generation_config=self.generation_config
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            result = json.loads(response_text)
            result['timestamp'] = timestamp
            
            logger.debug(f"Frame analysis at {timestamp:.2f}s: {result['segment_type']}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error at {timestamp:.2f}s: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._create_error_result(timestamp)
        except Exception as e:
            logger.error(f"Error analyzing frame at {timestamp:.2f}s: {e}")
            return self._create_error_result(timestamp)
    
    def _create_error_result(self, timestamp: float) -> Dict:
        """Create error result when analysis fails"""
        return {
            "timestamp": timestamp,
            "segment_type": "learning",
            "has_code": False,
            "code_content": None,
            "learning_topic": "Analysis failed",
            "confidence": 0.0,
            "language": "python",
            "code_complete": False
        }


class ConceptDetector:
    """Detect programming concepts from video transcripts and code segments"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
        }
    
    def detect_concepts(
        self,
        transcript: Optional[List[TranscriptEntry]],
        code_segments: List[CodeSegment]
    ) -> List[DetectedConcept]:
        """
        Detect programming concepts from transcript and code segments
        
        Args:
            transcript: List of transcript entries (optional)
            code_segments: List of code segments extracted from video
            
        Returns:
            List of detected concepts with timestamps
        """
        try:
            # Prepare text content for analysis
            transcript_text = ""
            if transcript:
                # Combine transcript entries
                transcript_text = " ".join([entry.text for entry in transcript])
            
            # Extract code content
            code_texts = []
            code_timestamps = []
            for seg in code_segments:
                if seg.code_content and seg.segment_type == 'code':
                    code_texts.append(seg.code_content)
                    code_timestamps.append(seg.timestamp)
            
            # Combine all text for analysis
            combined_text = transcript_text
            if code_texts:
                combined_text += "\n\nCode Examples:\n" + "\n---\n".join(code_texts[:10])  # Limit to first 10 code segments
            
            if not combined_text.strip():
                logger.warning("No content available for concept detection")
                return []
            
            # Create prompt for concept detection
            prompt = f"""Analyze this Python programming tutorial content and detect all programming concepts being taught.

Content:
{combined_text[:8000]}

Your task:
1. Identify all programming concepts mentioned or demonstrated (e.g., loops, arrays, recursion, functions, classes)
2. For each concept, identify the timestamps where it appears (use code segment timestamps as reference)
3. Categorize each concept
4. Provide confidence score (0.0-1.0) for each detection

Response format (JSON only, no markdown):
{{
    "concepts": [
        {{
            "concept_name": "loops",
            "category": "control_flow",
            "timestamps": [45.5, 120.3, 180.0],
            "confidence": 0.95,
            "description": "Teaching for loops and while loops"
        }}
    ]
}}

Focus on detecting: loops, arrays, lists, dictionaries, recursion, functions, classes, error handling, file operations, and other common Python concepts.
"""
            
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            # Convert to DetectedConcept objects
            detected_concepts = []
            for concept_data in result.get('concepts', []):
                # Map timestamps from code segments if available
                timestamps = concept_data.get('timestamps', [])
                
                # If no timestamps provided, try to infer from code segments
                if not timestamps and code_timestamps:
                    # Use code segment timestamps as fallback
                    timestamps = code_timestamps[:3]  # Use first few code timestamps
                
                detected_concepts.append(DetectedConcept(
                    concept_name=concept_data.get('concept_name', 'unknown'),
                    category=concept_data.get('category', 'general'),
                    timestamps=timestamps,
                    confidence=concept_data.get('confidence', 0.5),
                    description=concept_data.get('description')
                ))
            
            logger.info(f"Detected {len(detected_concepts)} concepts")
            return detected_concepts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse concept detection response: {e}")
            if 'response_text' in locals():
                logger.error(f"Response text: {response_text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error detecting concepts: {e}")
            return []


class VideoProcessor:
    """Process YouTube videos and extract frames"""
    
    def __init__(self, output_dir: str = "video_cache", service=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.service = service  # Reference to PauseToCodeService for progress tracking
        
    def download_video(self, youtube_url: str, video_id_for_progress: str = None, playlist_id: str = None) -> Tuple[str, Dict]:
        """Download YouTube video and return path + metadata
        
        Args:
            youtube_url: YouTube video URL
            video_id_for_progress: Optional video ID for progress tracking
            playlist_id: Optional playlist ID for folder organization
        """
        try:
            logger.info(f"Downloading video from: {youtube_url}")
            
            # Extract video ID - handle both individual videos and playlists
            video_id = None
            if 'v=' in youtube_url:
                video_id = youtube_url.split('v=')[-1].split('&')[0]
            elif 'youtu.be/' in youtube_url:
                video_id = youtube_url.split('youtu.be/')[-1].split('?')[0]
            else:
                video_id = youtube_url.split('/')[-1].split('?')[0]
            
            if not video_id_for_progress:
                video_id_for_progress = video_id
            
            # First, get metadata to extract title for filename
            logger.info(f"Fetching video metadata...")
            with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                # Handle playlist info extraction
                if info.get('_type') == 'playlist' and info.get('entries'):
                    info = info['entries'][0]
                    video_id = info.get('id', video_id)
                
                title = info.get('title', 'Unknown')
                
                # Sanitize title for filename (remove special characters)
                safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
                safe_title = safe_title.strip()[:100]  # Limit length to 100 chars
                
                metadata = {
                    "title": title,
                    "duration": info.get('duration', 0),
                    "author": info.get('uploader', 'Unknown'),
                    "views": info.get('view_count', 0),
                    "video_id": video_id
                }
            
            # Create folder structure: videos/{playlist_id}/{video_id}/video.mp4
            # Use simple safe names to avoid issues with special characters
            # Playlist folder: use playlist_id (first 20 chars) or 'single'
            # Video folder: use video_id (unique identifier)
            playlist_folder = playlist_id[:20] if playlist_id else 'single'
            video_folder = self.output_dir.resolve() / playlist_folder / video_id
            video_folder.mkdir(parents=True, exist_ok=True)
            
            # Always name the file 'video.mp4' inside the video's folder
            filename = "video.mp4"
            output_path = str(video_folder / filename)
            
            logger.info(f"📁 Folder structure:")
            logger.info(f"   Playlist folder: {playlist_folder}")
            logger.info(f"   Video folder: {video_id}")
            logger.info(f"   Full path: {output_path}")
            logger.info(f"   Folder created: {video_folder.exists()}")
            
            # Progress hook to update download status
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        # Get download progress percentage
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        
                        if total > 0:
                            progress_pct = int((downloaded / total) * 100)
                            
                            # Update progress tracking (0-100% for download)
                            if hasattr(self, 'service') and self.service and video_id_for_progress in self.service.processing_progress:
                                self.service.processing_progress[video_id_for_progress].update({
                                    'progress': progress_pct,
                                    'stage': f'Downloading: {progress_pct}%'
                                })
                            
                            logger.info(f"Download progress: {progress_pct}% ({downloaded}/{total} bytes)")
                    except Exception as e:
                        logger.error(f"Error in progress hook: {e}")
                
                elif d['status'] == 'finished':
                    logger.info(f"Download finished, now merging...")
                    if hasattr(self, 'service') and self.service and video_id_for_progress in self.service.processing_progress:
                        self.service.processing_progress[video_id_for_progress].update({
                            'progress': 100,
                            'stage': 'Download complete!'
                        })
            
            # Download with highest quality
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Highest quality
                'outtmpl': output_path,
                'merge_output_format': 'mp4',
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                'noplaylist': True,
                'playlist_items': '1',
                'progress_hooks': [progress_hook],
            }
            
            # Download video
            logger.info(f"Starting download...")
            logger.info(f"yt-dlp will download to: {output_path}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            
            # Verify file exists after download
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
                logger.info(f"✅ Video downloaded successfully: {output_path}")
                logger.info(f"✅ File size: {file_size:.2f} MB")
                logger.info(f"✅ File verified to exist on filesystem")
            else:
                logger.error(f"ERROR: Video file NOT found at expected path: {output_path}")
                logger.error(f"ERROR: Checking if file exists elsewhere...")
                # List all mp4 files in output directory
                all_mp4s = list(output_dir_abs.glob("*.mp4"))
                logger.error(f"ERROR: MP4 files in directory: {[f.name for f in all_mp4s]}")
                raise FileNotFoundError(f"Downloaded video not found at {output_path}")
            
            return output_path, metadata
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise
    
    def extract_transcript(self, youtube_url: str) -> Optional[List[Dict]]:
        """
        Extract transcript/captions from YouTube video
        Returns list of transcript entries with timestamps, or None if unavailable
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            List of dicts with 'timestamp', 'text', 'duration' or None if not available
        """
        try:
            logger.info(f"Attempting to extract transcript from: {youtube_url}")
            
            # Extract video ID
            video_id = None
            if 'v=' in youtube_url:
                video_id = youtube_url.split('v=')[-1].split('&')[0]
            elif 'youtu.be/' in youtube_url:
                video_id = youtube_url.split('youtu.be/')[-1].split('?')[0]
            else:
                video_id = youtube_url.split('/')[-1].split('?')[0]
            
            # Try to get transcript using yt-dlp
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                # Handle playlist info extraction
                if info.get('_type') == 'playlist' and info.get('entries'):
                    info = info['entries'][0]
                
                # Try to get automatic captions or manual captions
                subtitles = info.get('subtitles', {}) or info.get('automatic_captions', {})
                
                # Prefer English, but take any available language
                transcript_text = None
                transcript_lang = None
                
                if subtitles:
                    # Try English first
                    for lang_code in ['en', 'en-US', 'en-GB']:
                        if lang_code in subtitles:
                            transcript_lang = lang_code
                            break
                    
                    # If no English, take first available
                    if not transcript_lang and subtitles:
                        transcript_lang = list(subtitles.keys())[0]
                    
                    if transcript_lang:
                        # Download subtitle file
                        sub_opts = {
                            'quiet': True,
                            'skip_download': True,
                            'writesubtitles': True,
                            'writeautomaticsub': True,
                            'subtitleslangs': [transcript_lang],
                            'subtitlesformat': 'vtt',
                        }
                        
                        with yt_dlp.YoutubeDL(sub_opts) as sub_ydl:
                            sub_info = sub_ydl.extract_info(youtube_url, download=False)
                            
                            # Get subtitle URL
                            if transcript_lang in sub_info.get('subtitles', {}):
                                sub_url = sub_info['subtitles'][transcript_lang][0]['url']
                            elif transcript_lang in sub_info.get('automatic_captions', {}):
                                sub_url = sub_info['automatic_captions'][transcript_lang][0]['url']
                            else:
                                logger.warning(f"No transcript URL found for language {transcript_lang}")
                                return None
                            
                            # Download and parse VTT file
                            response = requests.get(sub_url, timeout=10)
                            if response.status_code == 200:
                                transcript_text = response.text
                            else:
                                logger.warning(f"Failed to download transcript: HTTP {response.status_code}")
                                return None
            
            if transcript_text:
                # Parse VTT format
                transcript_entries = self._parse_vtt_transcript(transcript_text)
                
                if transcript_entries:
                    logger.info(f"Successfully extracted {len(transcript_entries)} transcript entries")
                else:
                    logger.warning(f"Failed to parse transcript for video {video_id}")
            

            
        except Exception as e:
            logger.warning(f"Transcript extraction failed (non-critical): {e}")
            
        # Fallback: Try AI generation if no transcript found
        if not transcript_entries:
            logger.info("No transcript found on YouTube. Attempting AI generation with Gemini...")
            transcript_entries = self._generate_transcript_with_gemini(video_id)
            
        return transcript_entries

    def _generate_transcript_with_gemini(self, video_id: str) -> Optional[List[Dict]]:
        """
        Generate transcript using Gemini 2.5 Flash by processing the video file/audio.
        This is a fallback for videos with no subtitles.
        """
        try:
            # 1. Locate the video file
            playlist_id = self.output_dir.parent.name if self.output_dir.parent.name != 'videos' else None # Rough guess, better to look recursively
            # Safer way to find the file:
            video_files = list(self.output_dir.rglob(f"**/{video_id}/video.mp4"))
            if not video_files:
                logger.warning(f"Cannot generate AI transcript: Video file for {video_id} not found locally.")
                return None
            
            video_path = video_files[0]
            logger.info(f"Uploading video {video_id} to Gemini for transcription...")

            # 2. Upload file
            video_file = genai.upload_file(path=str(video_path))
            
            # Wait for processing
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                logger.error("Video processing failed in Gemini.")
                return None

            logger.info("Video processed by Gemini. Generating transcript...")

            # 3. Request Transcript
            # We use the same model as configured globally or instantiate a new one
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = """
            Listen to the audio of this video carefully and generate a complete transcript.
            Return the result as a raw JSON array of objects. 
            Do not use markdown code blocks. Just the raw JSON.
            Each object must have:
            - "timestamp": start time in seconds (float)
            - "text": the spoken text
            - "duration": approximate duration in seconds (float)
            
            Example format:
            [
                {"timestamp": 0.0, "text": "Hello world", "duration": 2.5},
                {"timestamp": 2.5, "text": "Welcome to Python", "duration": 3.0}
            ]
            """
            
            response = model.generate_content(
                [video_file, prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            
            # 4. Parse Response
            try:
                # Clean potential markdown
                text = response.text.replace('```json', '').replace('```', '').strip()
                transcript_data = json.loads(text)
                
                # Turn into TranscriptEntry format
                entries = []
                for item in transcript_data:
                    entries.append({
                        "timestamp": float(item.get("timestamp", 0.0)),
                        "text": str(item.get("text", "")),
                        "duration": float(item.get("duration", 0.0))
                    })
                
                logger.info(f"AI Transcript generated: {len(entries)} entries")
                
                # Cleanup: Delete the file from Gemini to save space/quota
                try:
                    genai.delete_file(video_file.name)
                except:
                    pass
                    
                return entries
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI transcript JSON: {response.text[:100]}...")
                return None
                
        except Exception as e:
            logger.error(f"AI Transcript generation failed: {e}")
            return None
    
    def _parse_vtt_transcript(self, vtt_content: str) -> List[Dict]:
        """
        Parse VTT (WebVTT) subtitle format into structured entries
        Returns list of dicts with timestamp, text, duration
        """
        entries = []
        lines = vtt_content.split('\n')
        
        # Pattern to match timestamp line: 00:00:12.500 --> 00:00:15.000
        timestamp_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line contains timestamps
            match = timestamp_pattern.match(line)
            if match:
                # Parse start and end times
                start_h, start_m, start_s, start_ms = map(int, match.groups()[:4])
                end_h, end_m, end_s, end_ms = map(int, match.groups()[4:])
                
                start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000.0
                end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000.0
                duration = end_time - start_time
                
                # Collect text lines until next timestamp or empty line
                text_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line or timestamp_pattern.match(next_line):
                        break
                    # Skip VTT formatting tags
                    if not next_line.startswith('<'):
                        text_lines.append(next_line)
                    i += 1
                
                text = ' '.join(text_lines).strip()
                
                if text:  # Only add non-empty entries
                    entries.append({
                        'timestamp': start_time,
                        'text': text,
                        'duration': duration
                    })
                
                continue
            
            i += 1
        
        return entries
    
    def extract_frame_at_timestamp(self, video_path: str, timestamp: float) -> Optional[np.ndarray]:
        """
        Extract a single frame at specific timestamp
        Returns frame as numpy array or None if failed
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        if timestamp > duration:
            logger.error(f"Timestamp {timestamp}s exceeds video duration {duration:.2f}s")
            cap.release()
            return None
        
        # Seek to timestamp
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            logger.info(f"Extracted frame at {timestamp}s (frame #{frame_number})")
            return frame
        else:
            logger.error(f"Failed to extract frame at {timestamp}s")
            return None
    
    def extract_frames_fixed_interval(
        self,
        video_path: str,
        interval_seconds: float = 2.0
    ) -> List[Tuple[np.ndarray, float, int]]:
        """
        Extract frames at fixed intervals (every N seconds)
        Optimized for precise timestamp queries
        Returns list of (frame, timestamp, frame_number)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        logger.info(f"Video info - FPS: {fps}, Duration: {duration:.2f}s, Total frames: {total_frames}")
        logger.info(f"Extracting frames every {interval_seconds}s")
        
        frames_data = []
        frame_interval = int(fps * interval_seconds)
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract frame at fixed intervals
            if frame_count % frame_interval == 0:
                frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                frames_data.append((frame.copy(), timestamp, frame_number))
            
            frame_count += 1
        
        cap.release()
        logger.info(f"Extracted {len(frames_data)} frames for analysis")
        return frames_data


class PauseToCodeService:
    """Main service orchestrating the pause-to-code feature"""
    
    def __init__(self, cache_dir: str = "codio_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.extractor = GeminiCodeExtractor()
        self.processor = VideoProcessor(str(self.cache_dir / "videos"), service=self)
        self.concept_detector = ConceptDetector()
        
        # Progress tracking for each video
        self.processing_progress = {}  # {video_id: {status, progress, stage, total_frames, current_frame}}
        
    def process_video(
        self,
        youtube_url: str,
        force_reprocess: bool = False,
        frame_interval: float = 2.0
    ) -> VideoAnalysis:
        """
        Process entire video and extract all code segments
        This creates the pre-extracted database
        
        Args:
            youtube_url: YouTube video URL
            force_reprocess: Force reprocessing even if cached
            frame_interval: Extract frames every N seconds (default: 2.0)
        """
        # Check cache first
        video_id = self._extract_video_id(youtube_url)
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        if cache_file.exists() and not force_reprocess:
            logger.info(f"Loading cached analysis for {video_id}")
            return self._load_cached_analysis(cache_file)
        
        # Initialize progress tracking
        self.processing_progress[video_id] = {
            'status': 'downloading',
            'progress': 0,
            'stage': 'Downloading video...',
            'total_frames': 0,
            'current_frame': 0
        }
        logger.info(f"STAGE 1/3: Downloading video {video_id}")
        
        try:
            # Extract playlist ID if it's from a playlist URL
            playlist_id = self._extract_playlist_id(youtube_url)
            # Download and process video
            video_path, metadata = self.processor.download_video(youtube_url, video_id, playlist_id)
            
            self.processing_progress[video_id].update({
                'status': 'extracting',
                'progress': 15,
                'stage': 'Extracting frames...'
            })
            logger.info(f"STAGE 2/3: Extracting frames from video")
            
            # Extract frames at fixed intervals
            frames_data = self.processor.extract_frames_fixed_interval(video_path, frame_interval)
            
            total_frames = len(frames_data)
            self.processing_progress[video_id].update({
                'status': 'analyzing',
                'progress': 20,
                'stage': f'Analyzing {total_frames} frames with AI...',
                'total_frames': total_frames,
                'current_frame': 0
            })
            logger.info(f"🤖 STAGE 3/3: Analyzing {total_frames} frames with Gemini AI")
            logger.info(f"{'='*60}")
            
            # Analyze each frame
            code_segments = []
            prev_code = None
            
            for idx, (frame, timestamp, frame_number) in enumerate(frames_data):
                current_frame = idx + 1
                progress = 20 + int((current_frame / total_frames) * 75)  # 20% to 95%
                
                self.processing_progress[video_id].update({
                    'progress': progress,
                    'current_frame': current_frame,
                    'stage': f'Analyzing frame {current_frame}/{total_frames}'
                })
                
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                logger.info(f"📊 Frame {current_frame}/{total_frames} ({progress}%) - Timestamp {minutes:02d}:{seconds:02d}")
                
                analysis = self.extractor.analyze_frame(frame, timestamp)
                
                # Create code segment
                segment = CodeSegment(
                    timestamp=timestamp,
                    frame_number=frame_number,
                    segment_type=analysis['segment_type'],
                    code_content=analysis.get('code_content'),
                    learning_topic=analysis.get('learning_topic'),
                    confidence=analysis.get('confidence', 0.0),
                    language=analysis.get('language', 'python'),
                    code_complete=analysis.get('code_complete', False)
                )
                
                # Add all segments for precise timestamp queries
                code_segments.append(segment)
                if segment.code_content:
                    prev_code = segment.code_content
            
            # Extract transcript (optional, non-blocking)
            transcript_entries = None
            try:
                logger.info("Extracting transcript...")
                transcript_data = self.processor.extract_transcript(youtube_url)
                if transcript_data:
                    transcript_entries = [TranscriptEntry(**entry) for entry in transcript_data]
                    logger.info(f"Transcript extracted: {len(transcript_entries)} entries")
                else:
                    logger.info("No transcript available for this video")
            except Exception as e:
                logger.warning(f"Transcript extraction failed (non-critical): {e}")
                transcript_entries = None
            
            # Create video analysis
            video_analysis = VideoAnalysis(
                video_id=video_id,
                video_title=metadata['title'],
                duration=metadata['duration'],
                total_frames_analyzed=len(frames_data),
                code_segments=code_segments,
                metadata=metadata,
                extraction_date=datetime.now().isoformat(),
                transcript=transcript_entries,
                detected_concepts=None  # Will be populated later if concept detection is run
            )
            
            # Update progress to completed
            self.processing_progress[video_id].update({
                'status': 'completed',
                'progress': 95,
                'stage': 'Saving analysis...'
            })
            logger.info(f"Saving analysis to cache...")
            
            # Cache the analysis
            self._cache_analysis(video_analysis, cache_file)
            
            self.processing_progress[video_id].update({
                'status': 'completed',
                'progress': 100,
                'stage': 'Completed!'
            })
            logger.info(f"{'='*60}")
            logger.info(f"VIDEO PROCESSING COMPLETE!")
            logger.info(f"   Video ID: {video_id}")
            logger.info(f"   Title: {metadata['title']}")
            logger.info(f"   Duration: {int(metadata['duration']//60)}m {int(metadata['duration']%60)}s")
            logger.info(f"   Frames Analyzed: {len(frames_data)}")
            logger.info(f"   Code Segments Found: {sum(1 for s in code_segments if s.code_content)}")
            logger.info(f"{'='*60}")
            
            # Keep video file for pause-to-code feature (don't delete)
            logger.info(f"Video file kept at: {video_path}")
            
            return video_analysis
        
        except Exception as e:
            # Clean up failed processing from progress tracking
            logger.error(f"Video processing failed for {video_id}: {e}")
            if video_id in self.processing_progress:
                del self.processing_progress[video_id]
            raise
    
    def download_video_only(
        self,
        youtube_url: str
    ) -> Dict:
        """
        Download video without processing (lazy loading approach)
        Only downloads the video file and creates minimal cache entry
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Dict with video_id, status, title, duration
        """
        video_id = self._extract_video_id(youtube_url)
        playlist_id = self._extract_playlist_id(youtube_url)
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        # Check if already downloaded (look for video.mp4 in video's folder)
        playlist_folder = playlist_id[:20] if playlist_id else 'single'
        video_folder = self.cache_dir / "videos" / playlist_folder / video_id
        video_file = video_folder / "video.mp4"
        
        if video_file.exists() and cache_file.exists():
            logger.info(f"Video {video_id} already downloaded at {video_file}")
            analysis = self._load_cached_analysis(cache_file)
            
            # CHECK FOR MISSING DATA (Backfill)
            data_updated = False
            
            # 1. Backfill Transcript if missing
            if not analysis.transcript:
                logger.info(f"Backfilling missing transcript for {video_id}...")
                transcript_data = self.processor.extract_transcript(youtube_url)
                if transcript_data:
                    analysis.transcript = [TranscriptEntry(**entry) for entry in transcript_data]
                    logger.info(f"Transcript backfilled: {len(analysis.transcript)} entries")
                    data_updated = True
            
            # 2. Backfill Concepts if missing (and transcript exists)
            if not analysis.detected_concepts and analysis.transcript:
                logger.info(f"Backfilling missing concepts for {video_id}...")
                detected_concepts = self.concept_detector.detect_concepts(
                    transcript=analysis.transcript,
                    code_segments=analysis.code_segments or []
                )
                if detected_concepts:
                    analysis.detected_concepts = detected_concepts
                    logger.info(f"Concepts backfilled: {len(detected_concepts)} concepts")
                    data_updated = True
            
            # Save if updated
            if data_updated:
                self._cache_analysis(analysis, cache_file)
                logger.info(f"Cache updated with backfilled data")
            
            return {
                'video_id': video_id,
                'status': 'completed',
                'title': analysis.video_title,
                'duration': analysis.duration,
                'message': 'Video downloaded successfully'
            }
        
        # Initialize progress tracking
        self.processing_progress[video_id] = {
            'status': 'downloading',
            'progress': 0,
            'stage': 'Downloading video...',
            'total_frames': 0,
            'current_frame': 0
        }
        logger.info(f"Starting download for video {video_id}")
        
        try:
            # Extract playlist ID if it's from a playlist URL
            playlist_id = self._extract_playlist_id(youtube_url)
            # Download video
            downloaded_path, metadata = self.processor.download_video(youtube_url, video_id, playlist_id)
            
            # EXTRACT TRANSCRIPT (Lazy Loading Enhancement)
            logger.info("Extracting transcript...")
            self.processing_progress[video_id]['stage'] = 'Extracting transcript...'
            transcript_entries = None
            try:
                transcript_data = self.processor.extract_transcript(youtube_url)
                if transcript_data:
                    transcript_entries = [TranscriptEntry(**entry) for entry in transcript_data]
                    logger.info(f"Transcript extracted: {len(transcript_entries)} entries")
            except Exception as e:
                logger.warning(f"Transcript extraction failed: {e}")
            
            # DETECT CONCEPTS (Lazy Loading Enhancement)
            detected_concepts = None
            if transcript_entries:
                logger.info("Detecting concepts from transcript...")
                self.processing_progress[video_id]['stage'] = 'Detecting concepts...'
                try:
                    detected_concepts = self.concept_detector.detect_concepts(
                        transcript=transcript_entries,
                        code_segments=[]  # No code segments yet in lazy load
                    )
                    logger.info(f"Concepts detected: {len(detected_concepts) if detected_concepts else 0}")
                except Exception as e:
                    logger.warning(f"Concept detection failed: {e}")

            # Create minimal cache entry (no frames analyzed yet)
            video_analysis = VideoAnalysis(
                video_id=video_id,
                video_title=metadata['title'],
                duration=metadata['duration'],
                total_frames_analyzed=0,
                code_segments=[],
                metadata=metadata,
                extraction_date=datetime.now().isoformat(),
                transcript=transcript_entries,
                detected_concepts=detected_concepts
            )
            
            # Cache the minimal analysis
            self._cache_analysis(video_analysis, cache_file)
            
            # Mark as completed
            self.processing_progress[video_id].update({
                'status': 'completed',
                'progress': 100,
                'stage': 'Download complete!'
            })
            logger.info(f"Video downloaded: {metadata['title']}")
        except Exception as e:
            # Clean up failed download from progress tracking
            logger.error(f"Download failed for {video_id}: {e}")
            if video_id in self.processing_progress:
                del self.processing_progress[video_id]
            raise
        
        return {
            'video_id': video_id,
            'status': 'completed',
            'title': metadata['title'],
            'duration': metadata['duration'],
            'message': 'Video downloaded successfully'
        }
    
    def get_code_at_timestamp(
        self,
        video_id: str,
        timestamp: float,
        tolerance: float = 1.0
    ) -> Dict:
        """
        Get code at specific timestamp from pre-extracted data
        Returns the nearest code segment within tolerance
        """
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        if not cache_file.exists():
            return {
                "error": "Video not processed yet",
                "video_id": video_id,
                "message": "Please process the video first using process_video()"
            }
        
        analysis = self._load_cached_analysis(cache_file)
        
        # Find nearest segment within tolerance
        nearest_segment = None
        min_diff = float('inf')
        
        for segment in analysis.code_segments:
            diff = abs(segment.timestamp - timestamp)
            if diff < min_diff and diff <= tolerance:
                min_diff = diff
                nearest_segment = segment
        
        if nearest_segment is None:
            return {
                "found": False,
                "message": f"No segment found within {tolerance}s of {timestamp:.2f}s",
                "timestamp_requested": timestamp
            }
        
        # Return appropriate response based on segment type
        if nearest_segment.segment_type == "learning":
            return {
                "found": True,
                "timestamp_requested": timestamp,
                "timestamp_actual": nearest_segment.timestamp,
                "time_difference": min_diff,
                "segment_type": "learning",
                "message": "Learning phase - No code at this timestamp",
                "learning_topic": nearest_segment.learning_topic,
                "confidence": nearest_segment.confidence
            }
        else:
            return {
                "found": True,
                "timestamp_requested": timestamp,
                "timestamp_actual": nearest_segment.timestamp,
                "time_difference": min_diff,
                "segment_type": "code",
                "code_content": nearest_segment.code_content,
                "confidence": nearest_segment.confidence,
                "language": nearest_segment.language,
                "code_complete": nearest_segment.code_complete
            }
    
    def get_all_code_segments(self, video_id: str) -> List[Dict]:
        """Get all code segments for a video"""
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        if not cache_file.exists():
            return []
        
        analysis = self._load_cached_analysis(cache_file)
        return [asdict(segment) for segment in analysis.code_segments]
    
    def export_code_timeline(self, video_id: str, output_file: str):
        """Export all code in timeline format"""
        segments = self.get_all_code_segments(video_id)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Code Timeline for Video: {video_id}\n")
            f.write(f"# Generated: {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            for segment in segments:
                timestamp = segment['timestamp']
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                
                f.write(f"\n## Timestamp: {minutes:02d}:{seconds:02d} ({timestamp:.2f}s)\n")
                f.write(f"## Type: {segment['segment_type']}\n")
                f.write(f"## Confidence: {segment['confidence']:.2%}\n")
                
                if segment['code_content']:
                    f.write(f"## Code Complete: {segment['code_complete']}\n\n")
                    f.write("```python\n")
                    f.write(segment['code_content'])
                    f.write("\n```\n")
                
                if segment.get('learning_topic'):
                    f.write(f"\n### Learning Topic: {segment['learning_topic']}\n")
                
                f.write("\n" + "-" * 80 + "\n")
        
        logger.info(f"Code timeline exported to {output_file}")
    
    def search_transcript(self, video_id: str, query: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Search transcript by keywords
        
        Args:
            video_id: Video ID to search
            query: Search query (keywords)
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of matching transcript entries with timestamps
        """
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        if not cache_file.exists():
            return []
        
        analysis = self._load_cached_analysis(cache_file)
        
        if not analysis.transcript:
            return []
        
        # Prepare query
        if not case_sensitive:
            query = query.lower()
        
        # Search transcript entries
        matches = []
        for entry in analysis.transcript:
            text_to_search = entry.text if case_sensitive else entry.text.lower()
            
            if query in text_to_search:
                matches.append({
                    'timestamp': entry.timestamp,
                    'text': entry.text,
                    'duration': entry.duration,
                    'match_start': text_to_search.find(query) if case_sensitive else entry.text.lower().find(query),
                    'match_length': len(query)
                })
        
        logger.info(f"Found {len(matches)} transcript matches for query '{query}'")
        return matches
    
    def detect_and_store_concepts(self, video_id: str) -> List[DetectedConcept]:
        """
        Detect concepts for a video and update cache
        
        Args:
            video_id: Video ID to analyze
            
        Returns:
            List of detected concepts
        """
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        if not cache_file.exists():
            logger.error(f"Video {video_id} not found in cache")
            return []
        
        analysis = self._load_cached_analysis(cache_file)
        
        # Detect concepts
        logger.info(f"Detecting concepts for video {video_id}...")
        detected_concepts = self.concept_detector.detect_concepts(
            transcript=analysis.transcript,
            code_segments=analysis.code_segments
        )
        
        # Update analysis with detected concepts
        analysis.detected_concepts = detected_concepts
        
        # Save updated analysis to cache
        self._cache_analysis(analysis, cache_file)
        
        logger.info(f"Detected {len(detected_concepts)} concepts and updated cache")
        return detected_concepts
    
    def get_detected_concepts(self, video_id: str) -> List[Dict]:
        """
        Get detected concepts for a video
        
        Args:
            video_id: Video ID
            
        Returns:
            List of detected concepts (as dicts)
        """
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        if not cache_file.exists():
            return []
        
        analysis = self._load_cached_analysis(cache_file)
        
        if not analysis.detected_concepts:
            return []
        
        return [asdict(concept) for concept in analysis.detected_concepts]
    
    def _extract_video_id(self, youtube_url: str) -> str:
        """Extract video ID from YouTube URL"""
        if 'youtu.be/' in youtube_url:
            return youtube_url.split('youtu.be/')[1].split('?')[0]
        elif 'v=' in youtube_url:
            return youtube_url.split('v=')[1].split('&')[0]
        else:
            return hashlib.md5(youtube_url.encode()).hexdigest()
    
    def _extract_playlist_id(self, youtube_url: str) -> Optional[str]:
        """Extract playlist ID from YouTube URL"""
        import re
        # Match playlist ID pattern: list=XXXXX
        match = re.search(r'[?&]list=([^&]+)', youtube_url)
        if match:
            return match.group(1)
        return None
    
    def _cache_analysis(self, analysis: VideoAnalysis, cache_file: Path):
        """Save analysis to cache"""
        data = {
            'video_id': analysis.video_id,
            'video_title': analysis.video_title,
            'duration': analysis.duration,
            'total_frames_analyzed': analysis.total_frames_analyzed,
            'code_segments': [asdict(seg) for seg in analysis.code_segments],
            'metadata': analysis.metadata,
            'extraction_date': analysis.extraction_date
        }
        
        # Add optional transcript if available
        if analysis.transcript:
            data['transcript'] = [asdict(entry) for entry in analysis.transcript]
        
        # Add optional detected concepts if available
        if analysis.detected_concepts:
            data['detected_concepts'] = [asdict(concept) for concept in analysis.detected_concepts]
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis cached to {cache_file}")
    
    def _load_cached_analysis(self, cache_file: Path) -> VideoAnalysis:
        """Load analysis from cache"""
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = [CodeSegment(**seg) for seg in data['code_segments']]
        
        # Load optional transcript (backward compatible)
        transcript = None
        if 'transcript' in data and data['transcript']:
            transcript = [TranscriptEntry(**entry) for entry in data['transcript']]
        
        # Load optional detected concepts (backward compatible)
        detected_concepts = None
        if 'detected_concepts' in data and data['detected_concepts']:
            detected_concepts = [DetectedConcept(**concept) for concept in data['detected_concepts']]
        
        return VideoAnalysis(
            video_id=data['video_id'],
            video_title=data['video_title'],
            duration=data['duration'],
            total_frames_analyzed=data['total_frames_analyzed'],
            code_segments=segments,
            metadata=data['metadata'],
            extraction_date=data['extraction_date'],
            transcript=transcript,
            detected_concepts=detected_concepts
        )
    
    def get_playlist_videos(self, playlist_url: str) -> Dict:
        """
        Extract list of videos from a YouTube playlist
        Returns playlist metadata and video list without downloading
        """
        try:
            logger.info(f"Extracting playlist info from: {playlist_url}")
            
            ydl_opts = {
                'extract_flat': True,  # Don't download, just get metadata
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                
                # Handle single video URL
                if info.get('_type') != 'playlist':
                    video_title = info.get('title', 'Unknown')
                    return {
                        'playlist_title': video_title,
                        'videos': [{
                            'video_id': info.get('id'),
                            'title': video_title,
                            'thumbnail': info.get('thumbnail', ''),
                            'duration': info.get('duration', 0),
                            'url': f"https://www.youtube.com/watch?v={info.get('id')}"
                        }]
                    }
                
                # Handle playlist
                playlist_title = info.get('title', 'Unknown Playlist')
                videos = []
                for entry in info.get('entries', []):
                    if entry:
                        videos.append({
                            'video_id': entry.get('id'),
                            'title': entry.get('title', 'Unknown'),
                            'thumbnail': entry.get('thumbnail', ''),
                            'duration': entry.get('duration', 0),
                            'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
                        })
                
                logger.info(f"Found {len(videos)} videos in playlist: {playlist_title}")
                return {
                    'playlist_title': playlist_title,
                    'videos': videos
                }
                
        except Exception as e:
            logger.error(f"Error extracting playlist: {e}")
            raise
    
    def get_video_status(self, video_id: str) -> Dict:
        """
        Get processing status of a video
        Returns status: not_found, processing, or completed with real-time progress
        """
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        if cache_file.exists():
            return {
                "video_id": video_id,
                "status": "completed",
                "progress": 100.0,
                "stage": "Ready for pause-to-code"
            }
        
        # Check if video is being actively processed
        if video_id in self.processing_progress:
            progress_info = self.processing_progress[video_id]
            return {
                "video_id": video_id,
                "status": progress_info['status'],
                "progress": progress_info['progress'],
                "stage": progress_info['stage'],
                "current_frame": progress_info.get('current_frame', 0),
                "total_frames": progress_info.get('total_frames', 0)
            }
        
        # Check if video file exists (processing might have started)
        # Look for any file starting with video_id (filename includes title)
        video_dir = self.cache_dir / "videos"
        video_files = list(video_dir.glob(f"{video_id}*.mp4"))
        if video_files:
            return {
                "video_id": video_id,
                "status": "processing",
                "progress": 10.0,
                "stage": "Processing..."
            }
        
        return {
            "video_id": video_id,
            "status": "not_found",
            "progress": 0.0,
            "stage": "Not started"
        }
    
    def cancel_video_processing(self, video_id: str):
        """
        Cancel ongoing video processing
        Clean up partial downloads and processing
        """
        logger.info(f"🛑 Cancelling processing for video: {video_id}")
        
        # Remove from progress tracking
        if video_id in self.processing_progress:
            del self.processing_progress[video_id]
            logger.info(f"Removed from progress tracking")
        
        # Remove video file if exists
        video_path = self.cache_dir / "videos" / f"{video_id}.mp4"
        if video_path.exists():
            video_path.unlink()
            logger.info(f"Removed video file: {video_path}")
        
        # Remove partial files
        for part_file in self.cache_dir.glob(f"videos/{video_id}*"):
            if part_file.is_file():
                part_file.unlink()
                logger.info(f"Removed partial file: {part_file}")
            if part_file.is_file():
                part_file.unlink()
                logger.info(f"Removed partial file: {part_file}")
    
    def extract_frame_and_analyze(self, video_id: str, timestamp: float, playlist_id: str = None) -> Dict:
        """
        Extract frame at specific timestamp and analyze with VLM
        This is for real-time analysis when user pauses
        
        Args:
            video_id: YouTube video ID
            timestamp: Timestamp in seconds
            playlist_id: Optional playlist ID for locating video
        """
        try:
            # Find video file in folder structure: videos/{playlist_id}/{video_id}/video.mp4
            video_dir = self.cache_dir / "videos"
            video_file = None
            
            # Try with provided playlist_id first
            if playlist_id:
                playlist_folder = playlist_id[:20] if playlist_id else 'single'
                potential_path = video_dir / playlist_folder / video_id / "video.mp4"
                if potential_path.exists():
                    video_file = potential_path
                    logger.info(f"Found video at: {potential_path}")
            
            # If not found, search in 'single' folder
            if not video_file:
                potential_path = video_dir / "single" / video_id / "video.mp4"
                if potential_path.exists():
                    video_file = potential_path
                    logger.info(f"Found video in 'single' folder: {potential_path}")
            
            # If still not found, search all playlist folders
            if not video_file:
                logger.info(f"Searching all playlist folders for video {video_id}...")
                for playlist_folder in video_dir.iterdir():
                    if playlist_folder.is_dir():
                        potential_path = playlist_folder / video_id / "video.mp4"
                        if potential_path.exists():
                            video_file = potential_path
                            logger.info(f"Found video at: {potential_path}")
                            break
            
            if not video_file:
                logger.error(f"ERROR: Video {video_id} not found in any folder")
                return {
                    "error": "Video not downloaded yet",
                    "message": "The video is still processing. Please wait."
                }
            
            video_path = video_file  # Use found video file
            
            # Extract frame at timestamp
            frame = self.processor.extract_frame_at_timestamp(str(video_path), timestamp)
            
            if frame is None:
                return {
                    "error": "Failed to extract frame",
                    "message": "Could not extract frame at this timestamp"
                }
            
            # Analyze frame with Gemini
            analysis = self.extractor.analyze_frame(frame, timestamp)
            
            return {
                "timestamp": timestamp,
                "segment_type": analysis.get('segment_type'),
                "code_content": analysis.get('code_content'),
                "learning_topic": analysis.get('learning_topic'),
                "confidence": analysis.get('confidence', 0.0),
                "language": analysis.get('language', 'python'),
                "code_complete": analysis.get('code_complete', False)
            }
            
        except Exception as e:
            logger.error(f"Error extracting and analyzing frame: {e}")
            return {
                "error": str(e),
                "message": "Failed to analyze frame"
            }


# Example usage and API endpoints
def main():
    """Example usage of the Pause-to-Code service"""
    
    # Initialize service
    service = PauseToCodeService()
    
    # Example YouTube URL (replace with actual Python tutorial)
    youtube_url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
    
    # Step 1: Process video (do this once, it will cache)
    print("Processing video...")
    analysis = service.process_video(youtube_url)
    
    print(f"\nVideo Analysis Complete:")
    print(f"Title: {analysis.video_title}")
    print(f"Duration: {analysis.duration}s")
    print(f"Code segments found: {len(analysis.code_segments)}")
    
    # Step 2: Get code at specific timestamp (use this for pause-to-code)
    timestamp = 120.5  # 2 minutes 0.5 seconds
    result = service.get_code_at_timestamp(analysis.video_id, timestamp)
    
    print(f"\nCode at {timestamp}s:")
    print(json.dumps(result, indent=2))
    
    # Step 3: Export complete timeline
    service.export_code_timeline(
        analysis.video_id,
        f"{analysis.video_id}_timeline.md"
    )


if __name__ == "__main__":
    main()