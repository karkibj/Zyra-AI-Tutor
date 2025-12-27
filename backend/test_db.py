"""
Test database connection
"""
import asyncio
from app.db import init_db, get_db
from app.core.config import settings

async def test_connection():
    print(f"📊 Testing connection to: {settings.DATABASE_URL}")
    print(f"🏗️  Project: {settings.PROJECT_NAME}")
    print(f"🌍 Environment: {settings.ENV}")
    
    try:
        await init_db()
        print("✅ Database initialized successfully!")
        
        async for session in get_db():
            print("✅ Database session created successfully!")
            break
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_connection())