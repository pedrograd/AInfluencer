"""
Migration script to rename 'metadata' column to 'meta_data' in all tables
This fixes the SQLAlchemy reserved name conflict
"""
import sqlite3
from pathlib import Path

def migrate_database(db_path: str):
    """Migrate metadata column to meta_data in all tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tables that have metadata column
    tables = [
        'characters',
        'face_references',
        'media_items',
        'generation_jobs',
        'batch_jobs',
        'quality_scores',
        'scheduled_posts',
        'platform_accounts',
        'platform_posts'
    ]
    
    for table in tables:
        try:
            # Check if table exists and has metadata column
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            has_metadata = any(col[1] == 'metadata' for col in columns)
            has_meta_data = any(col[1] == 'meta_data' for col in columns)
            
            if has_metadata and not has_meta_data:
                print(f"Migrating {table}.metadata to {table}.meta_data...")
                cursor.execute(f"ALTER TABLE {table} RENAME COLUMN metadata TO meta_data")
                print(f"✅ Migrated {table}")
            elif has_meta_data:
                print(f"✅ {table} already has meta_data column")
            else:
                print(f"⚠️  {table} doesn't have metadata column")
        except Exception as e:
            print(f"❌ Error migrating {table}: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    # Find database file
    db_path = Path(__file__).parent / "ainfluencer.db"
    if not db_path.exists():
        db_path = Path(__file__).parent.parent / "ainfluencer.db"
    
    if db_path.exists():
        print(f"Migrating database: {db_path}")
        migrate_database(str(db_path))
    else:
        print("⚠️  Database file not found. Migration will happen automatically on first run.")
        print("   The new schema uses 'meta_data' instead of 'metadata'.")
