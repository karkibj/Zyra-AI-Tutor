"""
Admin Content Management API Endpoints
Handles content upload, management, and curriculum operations
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid
import os
from pathlib import Path
from datetime import datetime
import json

from app.db import get_db
from app.models.content import Content
from app.models.curriculum import CurriculumNode, ContentCurriculumMapping
from app.models.extracted_item import ExtractedItem
from app.models.processing_queue import ProcessingQueue

router = APIRouter(prefix="/admin/content", tags=["Admin Content Management"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

from pydantic import BaseModel

class ContentUploadResponse(BaseModel):
    id: str
    title: str
    content_type: str
    file_path: str
    processing_status: str
    created_at: datetime

class CurriculumNodeResponse(BaseModel):
    id: str
    code: str
    node_type: str
    name: str
    parent_id: Optional[str]
    content_count: int


# ============================================================================
# CONTENT UPLOAD
# ============================================================================

@router.post("/upload", response_model=ContentUploadResponse)
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    content_type: str = Form(...),
    description: Optional[str] = Form(None),
    curriculum_codes: str = Form("[]"),  # JSON array as string
    tags: str = Form("[]"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload new content to knowledge base
    
    - **file**: PDF, DOCX, etc.
    - **title**: Content title
    - **content_type**: curriculum|explanation|question|solution|past_paper|model_question|teacher_note
    - **curriculum_codes**: JSON array of curriculum codes (e.g., ["CDC-10-MATH-CH01"])
    - **tags**: JSON array of tags
    """
    try:
        # Parse JSON strings
        curriculum_codes_list = json.loads(curriculum_codes)
        tags_list = json.loads(tags)
        
        # Generate unique ID
        content_id = str(uuid.uuid4())
        
        # Save file
        upload_dir = Path("uploads/content")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = Path(file.filename).suffix
        file_path = upload_dir / f"{content_id}{file_extension}"
        
        # Write file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_size = len(content)
        
        # Create content record
        new_content = Content(
            id=content_id,
            title=title,
            description=description,
            content_type=content_type,
            file_path=str(file_path),
            file_type=file_extension[1:],  # Remove dot
            file_size=file_size,
            processing_status="pending",
            metadata={"tags": tags_list}
        )
        
        db.add(new_content)
        await db.flush()
        
        # Create curriculum mappings
        for code in curriculum_codes_list:
            result = await db.execute(
                select(CurriculumNode).where(CurriculumNode.code == code)
            )
            curriculum_node = result.scalar_one_or_none()
            
            if curriculum_node:
                mapping = ContentCurriculumMapping(
                    content_id=content_id,
                    curriculum_node_id=curriculum_node.id,
                    relevance_score=1.0,
                    tags=tags_list
                )
                db.add(mapping)
        
        # Add to processing queue
        queue_item = ProcessingQueue(
            content_id=content_id,
            task_type="extract_text",
            status="pending",
            priority=5
        )
        db.add(queue_item)
        
        await db.commit()
        
        return ContentUploadResponse(
            id=str(new_content.id),
            title=new_content.title,
            content_type=new_content.content_type,
            file_path=new_content.file_path,
            processing_status=new_content.processing_status,
            created_at=new_content.created_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LIST CONTENT
# ============================================================================

@router.get("/list")
async def list_content(
    content_type: Optional[str] = None,
    curriculum_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all content with optional filtering"""
    
    query = select(Content)
    
    # Apply filters
    if content_type:
        query = query.where(Content.content_type == content_type)
    
    if curriculum_code:
        query = query.join(ContentCurriculumMapping).join(CurriculumNode).where(
            CurriculumNode.code == curriculum_code
        )
    
    # Pagination
    query = query.order_by(Content.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    content_list = result.scalars().all()
    
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "content_type": c.content_type,
            "file_path": c.file_path,
            "processing_status": c.processing_status,
            "created_at": c.created_at.isoformat()
        }
        for c in content_list
    ]


# ============================================================================
# GET CURRICULUM TREE
# ============================================================================

@router.get("/curriculum/tree")
async def get_curriculum_tree(
    root_code: str = "CDC",
    db: AsyncSession = Depends(get_db)
):
    """Get hierarchical curriculum tree"""
    
    async def build_tree(node_id):
        # Get node
        result = await db.execute(
            select(CurriculumNode).where(CurriculumNode.id == node_id)
        )
        node = result.scalar_one()
        
        # Get content count
        result = await db.execute(
            select(func.count()).select_from(ContentCurriculumMapping)
            .where(ContentCurriculumMapping.curriculum_node_id == node_id)
        )
        content_count = result.scalar()
        
        # Get children
        result = await db.execute(
            select(CurriculumNode)
            .where(CurriculumNode.parent_id == node_id)
            .order_by(CurriculumNode.order_num)
        )
        children = result.scalars().all()
        
        return {
            "id": str(node.id),
            "code": node.code,
            "node_type": node.node_type,
            "name": node.name,
            "content_count": content_count,
            "children": [await build_tree(child.id) for child in children]
        }
    
    # Get root node
    result = await db.execute(
        select(CurriculumNode).where(CurriculumNode.code == root_code)
    )
    root = result.scalar_one_or_none()
    
    if not root:
        raise HTTPException(status_code=404, detail="Root node not found")
    
    return await build_tree(root.id)


# ============================================================================
# DASHBOARD STATS
# ============================================================================

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get comprehensive dashboard statistics"""
    
    # Total content count
    result = await db.execute(select(func.count()).select_from(Content))
    total_content = result.scalar()
    
    # By content type
    result = await db.execute(
        select(Content.content_type, func.count())
        .group_by(Content.content_type)
    )
    by_type = {row[0]: row[1] for row in result}
    
    # By processing status
    result = await db.execute(
        select(Content.processing_status, func.count())
        .group_by(Content.processing_status)
    )
    by_status = {row[0]: row[1] for row in result}
    
    # Recent uploads
    result = await db.execute(
        select(Content)
        .order_by(Content.created_at.desc())
        .limit(5)
    )
    recent = result.scalars().all()
    
    recent_uploads = [
        {
            "id": str(c.id),
            "title": c.title,
            "content_type": c.content_type,
            "created_at": c.created_at.isoformat()
        }
        for c in recent
    ]
    
    # Processing queue count
    result = await db.execute(
        select(func.count()).select_from(ProcessingQueue)
        .where(ProcessingQueue.status.in_(["pending", "processing"]))
    )
    processing_queue = result.scalar()
    
    return {
        "total_content": total_content,
        "by_type": by_type,
        "by_status": by_status,
        "recent_uploads": recent_uploads,
        "processing_queue": processing_queue
    }


# ============================================================================
# COVERAGE ANALYSIS
# ============================================================================

@router.get("/analytics/coverage")
async def get_coverage_analysis(db: AsyncSession = Depends(get_db)):
    """Analyze curriculum coverage by chapter"""
    
    # Get all chapters
    result = await db.execute(
        select(CurriculumNode)
        .where(
            CurriculumNode.node_type == "chapter",
            CurriculumNode.active == True
        )
        .order_by(CurriculumNode.order_num)
    )
    chapters = result.scalars().all()
    
    analysis = []
    for chapter in chapters:
        # Get content count for this chapter
        result = await db.execute(
            select(func.count()).select_from(ContentCurriculumMapping)
            .where(ContentCurriculumMapping.curriculum_node_id == chapter.id)
        )
        content_count = result.scalar()
        
        # Calculate coverage score
        score = min(100, content_count * 5)  # Simple scoring: 5 points per content
        
        status = "excellent" if score >= 80 else "good" if score >= 60 else "needs_attention"
        
        analysis.append({
            "chapter": chapter.name,
            "code": chapter.code,
            "content_count": content_count,
            "coverage_score": score,
            "status": status
        })
    
    return analysis