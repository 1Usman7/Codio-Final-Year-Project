#!/usr/bin/env python3
"""
Codio Pause-to-Code API Server
Flask REST API for video processing and code extraction
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from pathlib import Path
import traceback
from datetime import datetime
import os

# Import the main service
from pause_to_code_service import PauseToCodeService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize service
service = PauseToCodeService(cache_dir="codio_cache")

# Request tracking
request_log = []


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Codio Pause-to-Code API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


@app.route('/api/v1/video/process', methods=['POST'])
def process_video():
    """
    Process a YouTube video - supports both full processing and lazy loading
    
    Request body:
    {
        "youtube_url": "https://www.youtube.com/watch?v=...",
        "full_process": false (optional, default: false for lazy loading),
        "force_reprocess": false (optional)
    }
    
    Response:
    {
        "success": true,
        "video_id": "abc123",
        "video_title": "Python Tutorial",
        "duration": 600.5,
        "status": "completed",
        "message": "Video downloaded successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'youtube_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing youtube_url in request body"
            }), 400
        
        youtube_url = data['youtube_url']
        full_process = data.get('full_process', False)  # Default to lazy loading
        force_reprocess = data.get('force_reprocess', False)
        
        logger.info(f"Video request: {youtube_url} (full_process={full_process})")
        
        # Validate URL
        if not ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
            return jsonify({
                "success": False,
                "error": "Invalid YouTube URL"
            }), 400
        
        start_time = datetime.now()
        
        if full_process:
            # Full processing mode (extract all frames upfront)
            logger.info("🔄 Full processing mode")
            analysis = service.process_video(youtube_url, force_reprocess)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log request
            request_log.append({
                "timestamp": datetime.now().isoformat(),
                "endpoint": "/api/v1/video/process",
                "video_id": analysis.video_id,
                "processing_time": processing_time,
                "mode": "full"
            })
            
            return jsonify({
                "success": True,
                "video_id": analysis.video_id,
                "video_title": analysis.video_title,
                "duration": analysis.duration,
                "total_segments": len(analysis.code_segments),
                "processing_time": processing_time,
                "extraction_date": analysis.extraction_date,
                "status": "completed",
                "message": "Video processed successfully"
            }), 200
        else:
            # Lazy loading mode (download only, extract frames on-demand)
            logger.info("⚡ Lazy loading mode (download only)")
            result = service.download_video_only(youtube_url)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log request
            request_log.append({
                "timestamp": datetime.now().isoformat(),
                "endpoint": "/api/v1/video/process",
                "video_id": result['video_id'],
                "processing_time": processing_time,
                "mode": "lazy"
            })
            
            return jsonify({
                "success": True,
                **result,
                "processing_time": processing_time
            }), 200
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to process video"
        }), 500


@app.route('/api/v1/video/<video_id>/code', methods=['GET'])
def get_code_at_timestamp(video_id):
    """
    Get code at specific timestamp
    
    Query parameters:
    - timestamp: float (required) - timestamp in seconds
    - tolerance: float (optional, default=2.0) - tolerance in seconds
    
    Response:
    {
        "found": true,
        "timestamp_requested": 120.5,
        "timestamp_actual": 121.0,
        "time_difference": 0.5,
        "segment_type": "code",
        "code_content": "def hello():\n    print('Hello')",
        "explanation_text": null,
        "confidence": 0.95,
        "language": "python",
        "code_complete": true
    }
    """
    try:
        timestamp = request.args.get('timestamp', type=float)
        tolerance = request.args.get('tolerance', type=float, default=2.0)
        
        if timestamp is None:
            return jsonify({
                "success": False,
                "error": "Missing timestamp parameter"
            }), 400
        
        logger.info(f"Getting code for video {video_id} at timestamp {timestamp}s")
        
        result = service.get_code_at_timestamp(video_id, timestamp, tolerance)
        
        if "error" in result:
            return jsonify({
                "success": False,
                **result
            }), 404
        
        return jsonify({
            "success": True,
            **result
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting code at timestamp: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/video/<video_id>/segments', methods=['GET'])
def get_all_segments(video_id):
    """
    Get all code segments for a video
    
    Query parameters:
    - type: string (optional) - filter by segment type (code/explanation/mixed)
    - min_confidence: float (optional) - minimum confidence threshold
    
    Response:
    {
        "success": true,
        "video_id": "abc123",
        "total_segments": 45,
        "segments": [...]
    }
    """
    try:
        segment_type = request.args.get('type', type=str)
        min_confidence = request.args.get('min_confidence', type=float, default=0.0)
        
        logger.info(f"Getting all segments for video {video_id}")
        
        segments = service.get_all_code_segments(video_id)
        
        if not segments:
            return jsonify({
                "success": False,
                "error": "Video not found or not processed",
                "video_id": video_id
            }), 404
        
        # Apply filters
        if segment_type:
            segments = [s for s in segments if s['segment_type'] == segment_type]
        
        if min_confidence > 0:
            segments = [s for s in segments if s['confidence'] >= min_confidence]
        
        return jsonify({
            "success": True,
            "video_id": video_id,
            "total_segments": len(segments),
            "segments": segments
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting segments: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/video/<video_id>/timeline', methods=['GET'])
def get_code_timeline(video_id):
    """
    Get complete code timeline in markdown format
    
    Response: Markdown file download
    """
    try:
        output_file = f"timeline_{video_id}.md"
        service.export_code_timeline(video_id, output_file)
        
        if not os.path.exists(output_file):
            return jsonify({
                "success": False,
                "error": "Failed to generate timeline"
            }), 500
        
        return send_file(
            output_file,
            as_attachment=True,
            download_name=f"code_timeline_{video_id}.md",
            mimetype='text/markdown'
        )
        
    except Exception as e:
        logger.error(f"Error generating timeline: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/video/<video_id>/info', methods=['GET'])
def get_video_info(video_id):
    """
    Get video metadata and processing information
    
    Response:
    {
        "success": true,
        "video_id": "abc123",
        "video_title": "Python Tutorial",
        "duration": 600.5,
        "total_segments": 45,
        "metadata": {...},
        "extraction_date": "2025-01-01T12:00:00"
    }
    """
    try:
        cache_file = Path(service.cache_dir) / f"{video_id}_analysis.json"
        
        if not cache_file.exists():
            return jsonify({
                "success": False,
                "error": "Video not found",
                "video_id": video_id
            }), 404
        
        analysis = service._load_cached_analysis(cache_file)
        
        return jsonify({
            "success": True,
            "video_id": analysis.video_id,
            "video_title": analysis.video_title,
            "duration": analysis.duration,
            "total_segments": len(analysis.code_segments),
            "total_frames_analyzed": analysis.total_frames_analyzed,
            "metadata": analysis.metadata,
            "extraction_date": analysis.extraction_date
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/videos', methods=['GET'])
def list_processed_videos():
    """
    List all processed videos
    
    Response:
    {
        "success": true,
        "total_videos": 10,
        "videos": [
            {
                "video_id": "abc123",
                "video_title": "Python Tutorial",
                "duration": 600.5,
                "extraction_date": "2025-01-01T12:00:00"
            },
            ...
        ]
    }
    """
    try:
        cache_dir = Path(service.cache_dir)
        analysis_files = list(cache_dir.glob("*_analysis.json"))
        
        videos = []
        for file in analysis_files:
            try:
                analysis = service._load_cached_analysis(file)
                videos.append({
                    "video_id": analysis.video_id,
                    "video_title": analysis.video_title,
                    "duration": analysis.duration,
                    "total_segments": len(analysis.code_segments),
                    "extraction_date": analysis.extraction_date
                })
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "total_videos": len(videos),
            "videos": sorted(videos, key=lambda x: x['extraction_date'], reverse=True)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """
    Get API usage statistics
    
    Response:
    {
        "success": true,
        "total_requests": 100,
        "total_videos_processed": 10,
        "cache_size_mb": 1234.5,
        "recent_requests": [...]
    }
    """
    try:
        cache_dir = Path(service.cache_dir)
        
        # Calculate cache size
        total_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        cache_size_mb = total_size / (1024 * 1024)
        
        # Count processed videos
        analysis_files = list(cache_dir.glob("*_analysis.json"))
        
        return jsonify({
            "success": True,
            "total_requests": len(request_log),
            "total_videos_processed": len(analysis_files),
            "cache_size_mb": round(cache_size_mb, 2),
            "recent_requests": request_log[-10:]  # Last 10 requests
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "Please check the API documentation"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "Please try again later or contact support"
    }), 500


@app.route('/api/v1/playlist/videos', methods=['POST'])
def get_playlist_videos():
    """
    Extract video list from YouTube playlist
    
    Request body:
    {
        "playlist_url": "https://www.youtube.com/playlist?list=..."
    }
    
    Response:
    {
        "success": true,
        "videos": [
            {
                "video_id": "abc123",
                "title": "Video Title",
                "thumbnail": "https://...",
                "duration": 600
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'playlist_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing playlist_url in request body"
            }), 400
        
        playlist_url = data['playlist_url']
        videos = service.get_playlist_videos(playlist_url)
        
        return jsonify({
            "success": True,
            "videos": videos
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting playlist videos: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/video/<video_id>/status', methods=['GET'])
def get_video_status(video_id):
    """
    Get processing status of a video
    
    Response:
    {
        "success": true,
        "video_id": "abc123",
        "status": "processing|completed|not_found",
        "progress": 45.5
    }
    """
    try:
        status = service.get_video_status(video_id)
        
        return jsonify({
            "success": True,
            **status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting video status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/video/<video_id>/cancel', methods=['POST'])
def cancel_video_processing(video_id):
    """
    Cancel ongoing video processing
    
    Response:
    {
        "success": true,
        "message": "Processing cancelled"
    }
    """
    try:
        service.cancel_video_processing(video_id)
        
        return jsonify({
            "success": True,
            "message": "Processing cancelled"
        }), 200
        
    except Exception as e:
        logger.error(f"Error cancelling video: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/video/<video_id>/frame', methods=['GET'])
def get_frame_at_timestamp(video_id):
    """
    Extract and analyze frame at specific timestamp
    This is called when user pauses and video is already processed
    
    Query parameters:
    - timestamp: float (required) - timestamp in seconds
    
    Response:
    {
        "success": true,
        "code_content": "...",
        "segment_type": "code|learning"
    }
    """
    try:
        timestamp = request.args.get('timestamp', type=float)
        
        if timestamp is None:
            return jsonify({
                "success": False,
                "error": "Missing timestamp parameter"
            }), 400
        
        result = service.extract_frame_and_analyze(video_id, timestamp)
        
        return jsonify({
            "success": True,
            **result
        }), 200
        
    except Exception as e:
        logger.error(f"Error extracting frame: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    logger.info("Starting Codio Pause-to-Code API Server")
    logger.info("API Documentation: http://localhost:8080/health")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,  # Set to True for development
        threaded=True
    )