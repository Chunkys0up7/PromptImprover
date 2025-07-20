"""
Database migration script to add improvement_request column.
"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def migrate_database():
    """Add improvement_request column to existing database."""
    db_path = "prompt_storage.db"
    
    if not os.path.exists(db_path):
        logger.info("Database doesn't exist yet, no migration needed.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(prompts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'improvement_request' not in columns:
            logger.info("Adding improvement_request column to prompts table...")
            cursor.execute("ALTER TABLE prompts ADD COLUMN improvement_request TEXT")
            conn.commit()
            logger.info("Migration completed successfully!")
        else:
            logger.info("improvement_request column already exists.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 