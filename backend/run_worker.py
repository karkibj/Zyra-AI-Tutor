"""
Run Processing Worker
Processes content in background
"""
import asyncio
from app.workers.processing_worker import run_worker

if __name__ == "__main__":
    print("🚀 Starting Zyra Processing Worker...")
    asyncio.run(run_worker())