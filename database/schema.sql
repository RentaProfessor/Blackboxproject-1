-- BLACK BOX Project - Database Schema
-- SQLCipher encrypted database for secure local storage

-- ============================================================================
-- User Profiles
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences TEXT -- JSON blob for user preferences
);

-- ============================================================================
-- Conversation Context
-- ============================================================================
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT,
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_user_timestamp 
ON messages(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_messages_session 
ON messages(session_id);

-- ============================================================================
-- Reminders
-- ============================================================================
CREATE TABLE IF NOT EXISTS reminders (
    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed BOOLEAN DEFAULT 0,
    completed_at TIMESTAMP,
    recurring TEXT, -- 'daily', 'weekly', 'monthly', NULL
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reminders_user_due 
ON reminders(user_id, due_date);

CREATE INDEX IF NOT EXISTS idx_reminders_active 
ON reminders(user_id, completed, due_date);

-- ============================================================================
-- Secure Vault
-- ============================================================================
CREATE TABLE IF NOT EXISTS vault_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT, -- 'password', 'note', 'document', etc.
    content TEXT NOT NULL, -- Encrypted content
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_vault_user_category 
ON vault_items(user_id, category);

-- ============================================================================
-- Media Library
-- ============================================================================
CREATE TABLE IF NOT EXISTS media_items (
    media_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    type TEXT NOT NULL, -- 'music', 'podcast', 'audiobook', 'video'
    file_path TEXT NOT NULL,
    duration_seconds INTEGER,
    artist TEXT,
    album TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_played TIMESTAMP,
    play_count INTEGER DEFAULT 0,
    favorite BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_media_user_type 
ON media_items(user_id, type);

CREATE INDEX IF NOT EXISTS idx_media_favorites 
ON media_items(user_id, favorite, last_played DESC);

-- ============================================================================
-- Playback History
-- ============================================================================
CREATE TABLE IF NOT EXISTS playback_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    media_id INTEGER NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_played INTEGER, -- seconds
    completed BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (media_id) REFERENCES media_items(media_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_playback_user_date 
ON playback_history(user_id, played_at DESC);

-- ============================================================================
-- System Metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_type TEXT NOT NULL, -- 'latency', 'thermal', 'memory', etc.
    metric_value REAL NOT NULL,
    metadata TEXT -- JSON blob for additional data
);

CREATE INDEX IF NOT EXISTS idx_metrics_type_time 
ON metrics(metric_type, timestamp DESC);

-- ============================================================================
-- Function Call Log
-- ============================================================================
CREATE TABLE IF NOT EXISTS function_calls (
    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT,
    function_name TEXT NOT NULL,
    arguments TEXT, -- JSON blob
    result TEXT, -- JSON blob
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT 1,
    error TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_function_calls_user 
ON function_calls(user_id, timestamp DESC);

-- ============================================================================
-- Configuration Settings
-- ============================================================================
CREATE TABLE IF NOT EXISTS settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Initial Data
-- ============================================================================

-- Create default user
INSERT OR IGNORE INTO users (user_id, preferences) 
VALUES ('default_user', '{"theme": "high_contrast", "font_size": "large"}');

-- Default settings
INSERT OR IGNORE INTO settings (setting_key, setting_value) 
VALUES 
    ('db_version', '1.0.0'),
    ('encryption_enabled', 'true'),
    ('backup_enabled', 'true');

