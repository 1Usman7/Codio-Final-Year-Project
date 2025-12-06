#!/usr/bin/env python3
"""
Codio Pause-to-Code Backend Service
Complete implementation using Gemini 2.5 Pro API for VLM-based code extraction
"""

import os
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBZeilm4aGSwEaYXSH2g2Rh-10XtstWdDk"
genai.configure(api_key=GEMINI_API_KEY)


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
class VideoAnalysis:
    """Complete video analysis result"""
    video_id: str
    video_title: str
    duration: float
    total_frames_analyzed: int
    code_segments: List[CodeSegment]
    metadata: Dict
    extraction_date: str


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


class VideoProcessor:
    """Process YouTube videos and extract frames"""
    
    def __init__(self, output_dir: str = "video_cache", service=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.service = service  # Reference to PauseToCodeService for progress tracking
        
    def download_video(self, youtube_url: str, video_id_for_progress: str = None) -> Tuple[str, Dict]:
        """Download YouTube video and return path + metadata
        
        Args:
            youtube_url: YouTube video URL
            video_id_for_progress: Optional video ID for progress tracking
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
            
            # Create filename with video ID and title
            filename = f"{video_id}_{safe_title}.mp4"
            output_path = str(self.output_dir / filename)
            
            logger.info(f"Filename: {filename}")
            logger.info(f"Output path: {output_path}")
            
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
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            
            logger.info(f"Video downloaded successfully: {output_path}")
            return output_path, metadata
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise
    
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
            logger.info(f"✓ Loading cached analysis for {video_id}")
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
        
        # Download and process video
        video_path, metadata = self.processor.download_video(youtube_url)
        
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
        
        # Create video analysis
        video_analysis = VideoAnalysis(
            video_id=video_id,
            video_title=metadata['title'],
            duration=metadata['duration'],
            total_frames_analyzed=len(frames_data),
            code_segments=code_segments,
            metadata=metadata,
            extraction_date=datetime.now().isoformat()
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
        
        # Cleanup video file
        if os.path.exists(video_path):
            os.remove(video_path)
            logger.info("Cleaned up video file")
        
        return video_analysis
    
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
        cache_file = self.cache_dir / f"{video_id}_analysis.json"
        
        # Check if already downloaded (look for any file starting with video_id)
        video_dir = self.cache_dir / "videos"
        video_files = list(video_dir.glob(f"{video_id}*.mp4"))
        if video_files and cache_file.exists():
            logger.info(f"✓ Video {video_id} already downloaded")
            analysis = self._load_cached_analysis(cache_file)
            return {
                'video_id': video_id,
                'status': 'completed',
                'title': analysis.video_title,
                'duration': analysis.duration,
                'message': 'Video already downloaded'
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
        
        # Download video
        downloaded_path, metadata = self.processor.download_video(youtube_url, video_id)
        
        # Create minimal cache entry (no frames analyzed yet)
        video_analysis = VideoAnalysis(
            video_id=video_id,
            video_title=metadata['title'],
            duration=metadata['duration'],
            total_frames_analyzed=0,
            code_segments=[],
            metadata=metadata,
            extraction_date=datetime.now().isoformat()
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
    
    def _extract_video_id(self, youtube_url: str) -> str:
        """Extract video ID from YouTube URL"""
        if 'youtu.be/' in youtube_url:
            return youtube_url.split('youtu.be/')[1].split('?')[0]
        elif 'v=' in youtube_url:
            return youtube_url.split('v=')[1].split('&')[0]
        else:
            return hashlib.md5(youtube_url.encode()).hexdigest()
    
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
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis cached to {cache_file}")
    
    def _load_cached_analysis(self, cache_file: Path) -> VideoAnalysis:
        """Load analysis from cache"""
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = [CodeSegment(**seg) for seg in data['code_segments']]
        
        return VideoAnalysis(
            video_id=data['video_id'],
            video_title=data['video_title'],
            duration=data['duration'],
            total_frames_analyzed=data['total_frames_analyzed'],
            code_segments=segments,
            metadata=data['metadata'],
            extraction_date=data['extraction_date']
        )
    
    def get_playlist_videos(self, playlist_url: str) -> List[Dict]:
        """
        Extract list of videos from a YouTube playlist
        Returns list of video metadata without downloading
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
                    return [{
                        'video_id': info.get('id'),
                        'title': info.get('title', 'Unknown'),
                        'thumbnail': info.get('thumbnail', ''),
                        'duration': info.get('duration', 0),
                        'url': f"https://www.youtube.com/watch?v={info.get('id')}"
                    }]
                
                # Handle playlist
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
                
                logger.info(f"Found {len(videos)} videos in playlist")
                return videos
                
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
    
    def extract_frame_and_analyze(self, video_id: str, timestamp: float) -> Dict:
        """
        Extract frame at specific timestamp and analyze with VLM
        This is for real-time analysis when user pauses
        """
        try:
            # Check if video exists (look for any file starting with video_id)
            video_dir = self.cache_dir / "videos"
            video_files = list(video_dir.glob(f"{video_id}*.mp4"))
            
            if not video_files:
                return {
                    "error": "Video not downloaded yet",
                    "message": "The video is still processing. Please wait."
                }
            
            video_path = video_files[0]  # Use first matching file
            
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