#!/usr/bin/env python3
"""
BLACK BOX - Database and Vault Initialization Script
Creates the secure SQLCipher database and initializes the vault system
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from database.db import Database


async def initialize_database(master_password: str):
    """
    Initialize the BLACK BOX database with encryption
    
    Args:
        master_password: Master password for vault encryption
    """
    print("=" * 80)
    print("BLACK BOX - Database Initialization")
    print("=" * 80)
    print()
    
    # Database configuration
    db_path = "/data/blackbox.db"
    encryption_key = os.getenv("DATABASE_ENCRYPTION_KEY")
    
    if not encryption_key:
        print("❌ ERROR: DATABASE_ENCRYPTION_KEY not set in environment")
        print("Please set this in your .env file before running this script")
        return False
    
    if encryption_key == "CHANGE_ME_USE_OPENSSL_RAND_HEX_32":
        print("❌ ERROR: DATABASE_ENCRYPTION_KEY is still the default value")
        print("Please generate a new encryption key:")
        print("  openssl rand -hex 32")
        print("Then update your .env file")
        return False
    
    try:
        print("🔐 Initializing encrypted database...")
        print(f"   Database path: {db_path}")
        print(f"   Encryption: AES-256 (SQLCipher)")
        print()
        
        # Create database instance
        database = Database(
            db_path=db_path,
            encryption_key=encryption_key
        )
        
        # Initialize database (creates schema, tables, etc.)
        await database.initialize()
        
        print("✅ Database schema created successfully")
        
        # Create default user
        print("👤 Creating default user profile...")
        
        # Add some initial data
        await database.add_message("default_user", "system", "Welcome to BLACK BOX! I'm your offline voice assistant.")
        
        print("✅ Default user profile created")
        
        # Test vault functionality
        print("🔒 Testing vault functionality...")
        
        # Hash the master password
        password_hash = database.hash_password(master_password)
        
        # Test password verification
        if database.verify_password(password_hash, master_password):
            print("✅ Vault password hashing working correctly")
        else:
            print("❌ ERROR: Password verification failed")
            return False
        
        # Store a test vault item
        await database.store_vault_item(
            user_id="default_user",
            title="Welcome Note",
            content="This is your secure vault. You can store passwords, notes, and other sensitive information here.",
            category="note"
        )
        
        print("✅ Test vault item stored successfully")
        
        # Close database
        await database.close()
        
        print()
        print("🎉 Database initialization completed successfully!")
        print()
        print("Your BLACK BOX system is now ready with:")
        print("  ✅ Encrypted SQLCipher database")
        print("  ✅ Default user profile")
        print("  ✅ Secure vault system")
        print("  ✅ Argon2id password hashing")
        print()
        print("You can now use the voice assistant!")
        print("  - Open browser: http://localhost:3000")
        print("  - Click 'PRESS TO SPEAK' to start")
        print("  - Say 'Open my vault' to access secure storage")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Database initialization failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check that all services are running: docker-compose ps")
        print("  2. Check logs: docker-compose logs orchestrator")
        print("  3. Verify .env file has correct DATABASE_ENCRYPTION_KEY")
        print("  4. Ensure /data directory is writable")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Initialize BLACK BOX database and vault system"
    )
    parser.add_argument(
        "--master-password",
        required=True,
        help="Master password for vault encryption (use quotes if it contains spaces)"
    )
    
    args = parser.parse_args()
    
    # Validate master password
    if len(args.master_password) < 8:
        print("❌ ERROR: Master password must be at least 8 characters long")
        sys.exit(1)
    
    if len(args.master_password) > 128:
        print("❌ ERROR: Master password must be less than 128 characters")
        sys.exit(1)
    
    # Run the initialization
    success = asyncio.run(initialize_database(args.master_password))
    
    if success:
        print("✅ Initialization completed successfully!")
        sys.exit(0)
    else:
        print("❌ Initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
