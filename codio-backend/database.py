#!/usr/bin/env python3
"""
Codio Database Layer
SQLite database for user playlists and progress tracking
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)


class CodioDatabase:
    """Database manager for Codio user data"""
    
    def __init__(self, db_path: str = "codio_cache/codio.db"):
        """Initialize database connection"""
        self.db_path = db_path
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"[Database] Initialized database at {db_path}")
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def _init_database(self):
        """Initialize database tables"""
        logger.info("[Database] Creating/verifying database tables...")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT NOT NULL
            )
        """)
        
        # Playlists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id TEXT PRIMARY KEY,
                playlist_url TEXT NOT NULL,
                playlist_title TEXT NOT NULL,
                total_videos INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # User playlists (junction table)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                playlist_id TEXT NOT NULL,
                first_accessed TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                FOREIGN KEY (user_email) REFERENCES users(email),
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
                UNIQUE(user_email, playlist_id)
            )
        """)
        
        # Video progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                playlist_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                watched_seconds REAL NOT NULL DEFAULT 0,
                duration REAL NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (user_email) REFERENCES users(email),
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
                UNIQUE(user_email, playlist_id, video_id)
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_playlists_user 
            ON user_playlists(user_email)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_progress_user 
            ON video_progress(user_email, playlist_id)
        """)
        conn.commit()
        conn.close()
        logger.info("[Database] Database tables created/verified successfully")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash
    
    def create_user(self, email: str, name: str, password: str) -> Dict:
        """Create a new user account"""
        logger.info(f"[Database] Creating new user: {email}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                conn.close()
                logger.warning(f"[Database] User {email} already exists")
                return {"success": False, "error": "Email already registered"}
            
            # Create new user
            now = datetime.now().isoformat()
            password_hash = self._hash_password(password)
            
            cursor.execute(
                "INSERT INTO users (email, name, password_hash, created_at, last_login) VALUES (?, ?, ?, ?, ?)",
                (email, name, password_hash, now, now)
            )
            
            conn.commit()
            conn.close()
            logger.info(f"[Database] User {email} created successfully")
            return {"success": True, "message": "User created successfully"}
            
        except Exception as e:
            logger.error(f"[Database] Error creating user: {e}")
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, email: str, password: str) -> Dict:
        """Authenticate user with email and password"""
        logger.info(f"[Database] Authenticating user: {email}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user
            cursor.execute("SELECT email, name, password_hash FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                logger.warning(f"[Database] User {email} not found")
                return {"success": False, "error": "Invalid email or password"}
            
            # Verify password
            if not self._verify_password(password, user['password_hash']):
                conn.close()
                logger.warning(f"[Database] Invalid password for {email}")
                return {"success": False, "error": "Invalid email or password"}
            
            # Update last login
            now = datetime.now().isoformat()
            cursor.execute("UPDATE users SET last_login = ? WHERE email = ?", (now, email))
            conn.commit()
            conn.close()
            
            logger.info(f"[Database] User {email} authenticated successfully")
            return {
                "success": True,
                "user": {
                    "email": user['email'],
                    "name": user['name']
                }
            }
            
        except Exception as e:
            logger.error(f"[Database] Error authenticating user: {e}")
            return {"success": False, "error": str(e)}
    
    def add_or_update_user(self, email: str, name: str) -> bool:
        """Add or update user information (legacy method for backward compatibility)"""
        logger.info(f"[Database] Adding/updating user: {email}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Check if user exists
            cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
            exists = cursor.fetchone()
            
            if exists:
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = ? WHERE email = ?",
                    (now, email)
                )
                logger.info(f"[Database] Updated last_login for {email}")
            else:
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (email, name, created_at, last_login) VALUES (?, ?, ?, ?)",
                    (email, name, now, now)
                )
                logger.info(f"[Database] Created new user {email}")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[Database] Error adding/updating user: {e}")
            return False
    
    def add_or_update_playlist(self, playlist_id: str, playlist_url: str, 
                               playlist_title: str, total_videos: int) -> bool:
        """Add or update playlist information"""
        logger.info(f"[Database] Adding/updating playlist: {playlist_id}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Check if playlist exists
            cursor.execute("SELECT playlist_id FROM playlists WHERE playlist_id = ?", (playlist_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing playlist
                cursor.execute(
                    """UPDATE playlists 
                       SET playlist_url = ?, playlist_title = ?, total_videos = ?, updated_at = ?
                       WHERE playlist_id = ?""",
                    (playlist_url, playlist_title, total_videos, now, playlist_id)
                )
                logger.info(f"[Database] Updated playlist {playlist_id}")
            else:
                # Insert new playlist
                cursor.execute(
                    """INSERT INTO playlists 
                       (playlist_id, playlist_url, playlist_title, total_videos, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (playlist_id, playlist_url, playlist_title, total_videos, now, now)
                )
                logger.info(f"[Database] Created new playlist {playlist_id}")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[Database] Error adding/updating playlist: {e}")
            return False
    
    def link_user_to_playlist(self, user_email: str, playlist_id: str) -> bool:
        """Link a user to a playlist (track access)"""
        logger.info(f"[Database] Linking user {user_email} to playlist {playlist_id}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Check if link exists
            cursor.execute(
                "SELECT id FROM user_playlists WHERE user_email = ? AND playlist_id = ?",
                (user_email, playlist_id)
            )
            exists = cursor.fetchone()
            
            if exists:
                # Update last accessed
                cursor.execute(
                    "UPDATE user_playlists SET last_accessed = ? WHERE user_email = ? AND playlist_id = ?",
                    (now, user_email, playlist_id)
                )
                logger.info(f"[Database] Updated last_accessed for link")
            else:
                # Create new link
                cursor.execute(
                    """INSERT INTO user_playlists 
                       (user_email, playlist_id, first_accessed, last_accessed)
                       VALUES (?, ?, ?, ?)""",
                    (user_email, playlist_id, now, now)
                )
                logger.info(f"[Database] Created new user-playlist link")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[Database] Error linking user to playlist: {e}")
            return False
    
    def save_video_progress(self, user_email: str, playlist_id: str, video_id: str,
                           watched_seconds: float, duration: float, completed: bool) -> bool:
        """Save or update video watch progress"""
        logger.info(f"[Database] Saving progress for {user_email}/{playlist_id}/{video_id}")
        logger.info(f"[Database] Progress: {watched_seconds}s / {duration}s, completed={completed}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Check if progress exists
            cursor.execute(
                """SELECT id FROM video_progress 
                   WHERE user_email = ? AND playlist_id = ? AND video_id = ?""",
                (user_email, playlist_id, video_id)
            )
            exists = cursor.fetchone()
            
            if exists:
                # Update existing progress
                cursor.execute(
                    """UPDATE video_progress 
                       SET watched_seconds = ?, duration = ?, completed = ?, last_updated = ?
                       WHERE user_email = ? AND playlist_id = ? AND video_id = ?""",
                    (watched_seconds, duration, 1 if completed else 0, now, 
                     user_email, playlist_id, video_id)
                )
                logger.info(f"[Database] Updated existing progress record")
            else:
                # Insert new progress
                cursor.execute(
                    """INSERT INTO video_progress 
                       (user_email, playlist_id, video_id, watched_seconds, duration, completed, last_updated)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_email, playlist_id, video_id, watched_seconds, duration, 
                     1 if completed else 0, now)
                )
                logger.info(f"[Database] Created new progress record")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[Database] Error saving video progress: {e}")
            return False
    
    def get_user_playlists(self, user_email: str) -> List[Dict]:
        """Get all playlists for a user with progress"""
        logger.info(f"[Database] Fetching playlists for user: {user_email}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get playlists with progress calculation
            cursor.execute("""
                SELECT 
                    p.playlist_id,
                    p.playlist_url,
                    p.playlist_title,
                    p.total_videos,
                    up.first_accessed,
                    up.last_accessed,
                    COUNT(CASE WHEN vp.completed = 1 THEN 1 END) as completed_videos
                FROM playlists p
                JOIN user_playlists up ON p.playlist_id = up.playlist_id
                LEFT JOIN video_progress vp ON p.playlist_id = vp.playlist_id 
                    AND vp.user_email = up.user_email
                WHERE up.user_email = ?
                GROUP BY p.playlist_id
                ORDER BY up.last_accessed DESC
            """, (user_email,))
            
            rows = cursor.fetchall()
            
            playlists = []
            for row in rows:
                completed = row['completed_videos']
                total = row['total_videos']
                progress_percentage = (completed / total * 100) if total > 0 else 0
                
                playlists.append({
                    'playlist_id': row['playlist_id'],
                    'playlist_url': row['playlist_url'],
                    'playlist_title': row['playlist_title'],
                    'total_videos': total,
                    'completed_videos': completed,
                    'progress_percentage': round(progress_percentage, 1),
                    'first_accessed': row['first_accessed'],
                    'last_accessed': row['last_accessed']
                })
            
            conn.close()
            logger.info(f"[Database] Found {len(playlists)} playlists for {user_email}")
            return playlists
        except Exception as e:
            logger.error(f"[Database] Error fetching user playlists: {e}")
            return []
    
    def get_playlist_progress(self, user_email: str, playlist_id: str) -> Dict:
        """Get detailed progress for a specific playlist"""
        logger.info(f"[Database] Fetching progress for {user_email}/{playlist_id}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all video progress for this playlist
            cursor.execute("""
                SELECT video_id, watched_seconds, duration, completed, last_updated
                FROM video_progress
                WHERE user_email = ? AND playlist_id = ?
            """, (user_email, playlist_id))
            
            rows = cursor.fetchall()
            
            progress = {}
            for row in rows:
                progress[row['video_id']] = {
                    'watchedSeconds': row['watched_seconds'],
                    'duration': row['duration'],
                    'completed': bool(row['completed']),
                    'lastUpdated': row['last_updated']
                }
            
            conn.close()
            logger.info(f"[Database] Found progress for {len(progress)} videos")
            return progress
        except Exception as e:
            logger.error(f"[Database] Error fetching playlist progress: {e}")
            return {}
    
    def delete_user_playlist(self, user_email: str, playlist_id: str) -> bool:
        """Delete a playlist from user's list (also removes progress)"""
        logger.info(f"[Database] Deleting playlist {playlist_id} for user {user_email}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete user-playlist link
            cursor.execute(
                "DELETE FROM user_playlists WHERE user_email = ? AND playlist_id = ?",
                (user_email, playlist_id)
            )
            
            # Delete associated progress
            cursor.execute(
                "DELETE FROM video_progress WHERE user_email = ? AND playlist_id = ?",
                (user_email, playlist_id)
            )
            
            conn.commit()
            conn.close()
            logger.info(f"[Database] Deleted playlist and progress successfully")
            return True
        except Exception as e:
            logger.error(f"[Database] Error deleting playlist: {e}")
            return False
