"""
Database migration script to add improvement_request column.
"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate the database to add new columns."""
    db_path = "prompt_storage.db"
    
    if not os.path.exists(db_path):
        logger.info("Database doesn't exist yet, no migration needed.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if improvement_request column exists
        cursor.execute("PRAGMA table_info(prompts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'improvement_request' not in columns:
            logger.info("Adding improvement_request column...")
            cursor.execute("ALTER TABLE prompts ADD COLUMN improvement_request TEXT")
            logger.info("✅ improvement_request column added successfully.")
        else:
            logger.info("improvement_request column already exists.")
        
        # Check if generation_process column exists
        if 'generation_process' not in columns:
            logger.info("Adding generation_process column...")
            cursor.execute("ALTER TABLE prompts ADD COLUMN generation_process TEXT")
            logger.info("✅ generation_process column added successfully.")
        else:
            logger.info("generation_process column already exists.")
        
        conn.commit()
        conn.close()
        logger.info("✅ Database migration completed successfully.")
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_database() 