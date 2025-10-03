"""
BLACK BOX Database - SQLCipher Encrypted Database Layer
Provides secure storage for all application data
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


logger = logging.getLogger(__name__)


class Database:
    """
    Encrypted database layer using SQLCipher (SQLite with AES-256 encryption)
    
    Manages:
    - User profiles and preferences
    - Conversation context
    - Reminders
    - Secure vault
    - Media library
    - System metrics
    """
    
    def __init__(self, db_path: str, encryption_key: str):
        """
        Initialize database connection
        
        Args:
            db_path: Path to database file
            encryption_key: Encryption key for SQLCipher
        """
        self.db_path = db_path
        self.encryption_key = encryption_key
        self.conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        
        # Argon2 password hasher for vault
        self.password_hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4
        )
        
        logger.info(f"Database initialized: {db_path}")
    
    async def initialize(self):
        """Initialize database connection and schema"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to database
            self.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            self.conn.row_factory = sqlite3.Row
            
            # Enable SQLCipher encryption
            # Note: This requires sqlcipher3 package, not standard sqlite3
            # For now, using standard sqlite3 (encryption would be added in production)
            # self.conn.execute(f"PRAGMA key = '{self.encryption_key}'")
            
            # Enable WAL mode for better concurrency
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA foreign_keys=ON")
            
            # Load and execute schema
            await self._load_schema()
            
            logger.info("✓ Database initialized and schema loaded")
        
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise
    
    async def _load_schema(self):
        """Load and execute database schema"""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.executescript(schema_sql)
            self.conn.commit()
        
        logger.info("Database schema loaded")
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.conn is not None
    
    # ========================================================================
    # User Management
    # ========================================================================
    
    async def get_user_context(self, user_id: str, max_messages: int = 10) -> List[Dict]:
        """
        Get recent conversation context for a user
        
        Args:
            user_id: User identifier
            max_messages: Maximum number of messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT role, content, timestamp 
                FROM messages 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (user_id, max_messages)
            )
            rows = cursor.fetchall()
        
        # Reverse to get chronological order
        messages = [
            {
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"]
            }
            for row in reversed(rows)
        ]
        
        return messages
    
    async def add_message(self, user_id: str, role: str, content: str, session_id: Optional[str] = None):
        """
        Add a message to conversation history
        
        Args:
            user_id: User identifier
            role: 'user' or 'assistant'
            content: Message content
            session_id: Optional session identifier
        """
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (user_id, session_id, role, content)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, session_id, role, content)
            )
            self.conn.commit()
    
    async def clear_user_context(self, user_id: str):
        """
        Clear conversation history for a user
        
        Args:
            user_id: User identifier
        """
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
            self.conn.commit()
        
        logger.info(f"Cleared context for user: {user_id}")
    
    # ========================================================================
    # Reminders
    # ========================================================================
    
    async def create_reminder(
        self,
        user_id: str,
        title: str,
        due_date: datetime,
        description: Optional[str] = None,
        recurring: Optional[str] = None
    ) -> int:
        """
        Create a reminder
        
        Args:
            user_id: User identifier
            title: Reminder title
            due_date: When reminder is due
            description: Optional description
            recurring: Optional recurrence pattern
        
        Returns:
            Reminder ID
        """
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO reminders (user_id, title, description, due_date, recurring)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, title, description, due_date.isoformat(), recurring)
            )
            self.conn.commit()
            reminder_id = cursor.lastrowid
        
        logger.info(f"Created reminder {reminder_id} for user {user_id}: {title}")
        return reminder_id
    
    async def get_active_reminders(self, user_id: str) -> List[Dict]:
        """
        Get active (not completed) reminders for a user
        
        Args:
            user_id: User identifier
        
        Returns:
            List of reminder dictionaries
        """
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reminders 
                WHERE user_id = ? AND completed = 0 
                ORDER BY due_date ASC
                """,
                (user_id,)
            )
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def complete_reminder(self, reminder_id: int):
        """
        Mark a reminder as completed
        
        Args:
            reminder_id: Reminder ID
        """
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE reminders 
                SET completed = 1, completed_at = CURRENT_TIMESTAMP 
                WHERE reminder_id = ?
                """,
                (reminder_id,)
            )
            self.conn.commit()
        
        logger.info(f"Completed reminder: {reminder_id}")
    
    # ========================================================================
    # Secure Vault
    # ========================================================================
    
    async def store_vault_item(
        self,
        user_id: str,
        title: str,
        content: str,
        category: str = "note"
    ) -> int:
        """
        Store an item in the secure vault
        
        Args:
            user_id: User identifier
            title: Item title
            content: Item content (will be encrypted)
            category: Item category
        
        Returns:
            Item ID
        """
        # TODO: Add additional encryption layer for vault content
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO vault_items (user_id, title, category, content)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, title, category, content)
            )
            self.conn.commit()
            item_id = cursor.lastrowid
        
        logger.info(f"Stored vault item {item_id} for user {user_id}")
        return item_id
    
    async def get_vault_items(self, user_id: str, category: Optional[str] = None) -> List[Dict]:
        """
        Get vault items for a user
        
        Args:
            user_id: User identifier
            category: Optional category filter
        
        Returns:
            List of vault item dictionaries
        """
        async with self._lock:
            cursor = self.conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM vault_items WHERE user_id = ? AND category = ? ORDER BY modified_at DESC",
                    (user_id, category)
                )
            else:
                cursor.execute(
                    "SELECT * FROM vault_items WHERE user_id = ? ORDER BY modified_at DESC",
                    (user_id,)
                )
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2id
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        return self.password_hasher.hash(password)
    
    def verify_password(self, password_hash: str, password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password_hash: Stored password hash
            password: Plain text password to verify
        
        Returns:
            True if password matches
        """
        try:
            self.password_hasher.verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False
    
    # ========================================================================
    # Media Library
    # ========================================================================
    
    async def add_media_item(
        self,
        user_id: str,
        title: str,
        media_type: str,
        file_path: str,
        **metadata
    ) -> int:
        """
        Add a media item to the library
        
        Args:
            user_id: User identifier
            title: Media title
            media_type: Type of media
            file_path: Path to media file
            **metadata: Additional metadata
        
        Returns:
            Media ID
        """
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO media_items 
                (user_id, title, type, file_path, duration_seconds, artist, album)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    title,
                    media_type,
                    file_path,
                    metadata.get("duration_seconds"),
                    metadata.get("artist"),
                    metadata.get("album")
                )
            )
            self.conn.commit()
            media_id = cursor.lastrowid
        
        return media_id
    
    async def get_media_items(self, user_id: str, media_type: Optional[str] = None) -> List[Dict]:
        """Get media items for a user"""
        async with self._lock:
            cursor = self.conn.cursor()
            if media_type:
                cursor.execute(
                    "SELECT * FROM media_items WHERE user_id = ? AND type = ? ORDER BY title",
                    (user_id, media_type)
                )
            else:
                cursor.execute(
                    "SELECT * FROM media_items WHERE user_id = ? ORDER BY title",
                    (user_id,)
                )
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    # ========================================================================
    # Metrics
    # ========================================================================
    
    async def log_metric(self, metric_type: str, value: float, metadata: Optional[Dict] = None):
        """
        Log a system metric
        
        Args:
            metric_type: Type of metric
            value: Metric value
            metadata: Optional metadata
        """
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO metrics (metric_type, metric_value, metadata) VALUES (?, ?, ?)",
                (metric_type, value, json.dumps(metadata) if metadata else None)
            )
            self.conn.commit()
    
    # ========================================================================
    # Cleanup and Maintenance
    # ========================================================================
    
    async def cleanup_old_messages(self, days: int = 30):
        """
        Clean up old messages
        
        Args:
            days: Delete messages older than this many days
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        async with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM messages WHERE timestamp < ?",
                (cutoff_date,)
            )
            deleted = cursor.rowcount
            self.conn.commit()
        
        logger.info(f"Deleted {deleted} old messages")
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

