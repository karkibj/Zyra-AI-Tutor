"""
Create a dummy user for testing (without auth)
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from sqlalchemy import text
import uuid


async def create_dummy_user():
    """Create a test user"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if users table exists
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                print("⚠️  Users table doesn't exist!")
                print("Creating users table...")
                
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE,
                        full_name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                await db.commit()
                print("✅ Users table created")
            
            # Create dummy user
            dummy_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
            
            await db.execute(text("""
                INSERT INTO users (id, username, email, full_name)
                VALUES (:id, :username, :email, :full_name)
                ON CONFLICT (id) DO NOTHING;
            """), {
                'id': dummy_id,
                'username': 'test_student',
                'email': 'test@zyra.local',
                'full_name': 'Test Student'
            })
            
            await db.commit()
            
            print("\n✅ SUCCESS!")
            print(f"   User ID: {dummy_id}")
            print(f"   Username: test_student")
            print(f"   Email: test@zyra.local")
            print("\n🎉 You can now use the chat!")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ ERROR: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_dummy_user())