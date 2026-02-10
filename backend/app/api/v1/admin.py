"""
Admin API for content upload and management
backend/app/api/v1/admin.py
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import json
import uuid
from pathlib import Path
from datetime import datetime

from app.db import get_db
from app.models.content import Content
from app.models.curriculum import CurriculumNode, ContentCurriculumMapping
from app.models.processing_queue import ProcessingQueue

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================================
# ENHANCED CONTENT UPLOAD
# ============================================================================

@router.post("/content/upload")
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    content_type: str = Form(...),
    description: Optional[str] = Form(None),
    curriculum_codes: str = Form("[]"),
    tags: str = Form("[]"),
    db: AsyncSession = Depends(get_db)
):
    """Upload new content to knowledge base"""
    
    content_uuid = None
    file_path = None
    
    try:
        # Parse JSON strings
        curriculum_codes_list = json.loads(curriculum_codes)
        tags_list = json.loads(tags)
        
        print(f"📤 Starting upload: {title}")
        print(f"   Type: {content_type}")
        print(f"   Chapters: {len(curriculum_codes_list)}")
        print(f"   Tags: {tags_list}")
        
        # Generate UUID (keep as UUID object)
        content_uuid = uuid.uuid4()
        
        # Save file
        upload_dir = Path("uploads/content")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = Path(file.filename).suffix
        file_path = upload_dir / f"{str(content_uuid)}{file_extension}"
        
        print(f"💾 Saving file to: {file_path}")
        
        # Write file
        with open(file_path, "wb") as buffer:
            content_bytes = await file.read()
            buffer.write(content_bytes)
        
        file_size = len(content_bytes)
        print(f"✅ File saved: {file_size} bytes")
        
        # Create content record (use UUID object directly)
        new_content = Content(
            id=content_uuid,
            title=title,
            description=description,
            content_type=content_type,
            file_path=str(file_path),
            file_type=file_extension[1:],
            file_size=file_size,
            processing_status="pending",
            content_metadata={"tags": tags_list, "original_filename": file.filename}
        )
        
        db.add(new_content)
        await db.flush()
        print(f"✅ Content record created: {content_uuid}")
        
        # Create curriculum mappings
        mapped_count = 0
        for code in curriculum_codes_list:
            try:
                result = await db.execute(
                    select(CurriculumNode).where(CurriculumNode.code == code)
                )
                curriculum_node = result.scalar_one_or_none()
                
                if curriculum_node:
                    mapping = ContentCurriculumMapping(
                        content_id=content_uuid,
                        curriculum_node_id=curriculum_node.id,
                        relevance_score=1.0,
                        tags=tags_list
                    )
                    db.add(mapping)
                    mapped_count += 1
                else:
                    print(f"⚠️ Chapter not found: {code}")
            except Exception as mapping_error:
                print(f"❌ Error mapping {code}: {mapping_error}")
        
        print(f"✅ Created {mapped_count} chapter mappings")
        
        # Add to processing queue
        try:
            queue_item = ProcessingQueue(
                content_id=content_uuid,
                task_type="extract_text",
                status="pending",
                priority=5
            )
            db.add(queue_item)
            print(f"✅ Added to processing queue")
        except Exception as queue_error:
            print(f"⚠️ Queue error (continuing anyway): {queue_error}")
        
        # Commit everything
        await db.commit()
        print(f"✅ Upload completed successfully!")
        
        return {
            "success": True,
            "id": str(content_uuid),
            "title": new_content.title,
            "content_type": new_content.content_type,
            "file_path": new_content.file_path,
            "processing_status": new_content.processing_status,
            "created_at": new_content.created_at.isoformat(),
            "chapters_mapped": mapped_count
        }
        
    except Exception as e:
        print(f"❌ Upload failed!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        await db.rollback()
        
        # Clean up file if it was created
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                print(f"🗑️ Cleaned up file: {file_path}")
            except:
                pass
        
        raise HTTPException(
            status_code=500, 
            detail=f"Upload failed: {str(e)}"
        )


# ============================================================================
# QUICK UPLOAD: PAST PAPER
# ============================================================================

@router.post("/upload/past-paper")
async def upload_past_paper(
    file: UploadFile = File(...),
    year: int = Form(...),
    province: str = Form(...),
    title: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Quick upload for past papers"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files allowed")
    
    if not title:
        title = f"SEE {year} Mathematics - {province} Province"
    
    print(f"📤 Uploading: {title}")
    print(f"   Year: {year}, Province: {province}")
    
    # Get all chapters
    result = await db.execute(
        select(CurriculumNode).where(
            CurriculumNode.code.like("CDC-10-MATH-CH%"),
            CurriculumNode.active == True
        )
    )
    chapters = result.scalars().all()
    
    # Generate UUID
    content_uuid = uuid.uuid4()
    
    # Save file
    upload_dir = Path("uploads/content")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{str(content_uuid)}.pdf"
    
    with open(file_path, "wb") as buffer:
        content_bytes = await file.read()
        buffer.write(content_bytes)
    
    # Create metadata
    metadata_dict = {
        "exam": {
            "year": year,
            "province": province,
            "full_marks": 75,
            "board": "CDC",
            "grade": 10,
            "subject": "Mathematics"
        },
        "original_filename": file.filename
    }
    
    # Create content record
    new_content = Content(
        id=content_uuid,
        title=title,
        content_type="past_paper",
        file_path=str(file_path),
        file_type="pdf",
        file_size=len(content_bytes),
        processing_status="pending",
        content_metadata=metadata_dict
    )
    
    db.add(new_content)
    await db.flush()
    
    # Map to chapters
    for chapter in chapters:
        mapping = ContentCurriculumMapping(
            content_id=content_uuid,
            curriculum_node_id=chapter.id,
            relevance_score=1.0,
            tags=["past_paper", f"year_{year}", province.lower()]
        )
        db.add(mapping)
    
    # Add to queue
    queue_item = ProcessingQueue(
        content_id=content_uuid,
        task_type="extract_text",
        status="pending",
        priority=8
    )
    db.add(queue_item)
    
    await db.commit()
    
    print(f"✅ Upload complete!")
    
    return {
        "success": True,
        "message": "Past paper uploaded successfully",
        "id": str(content_uuid),
        "title": title,
        "year": year,
        "province": province,
        "mapped_to_chapters": len(chapters)
    }


# ============================================================================
# LIST CONTENT
# ============================================================================

@router.get("/content/list")
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
    
    return {
        "total": len(content_list),
        "items": [
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
    }


# ============================================================================
# CURRICULUM TREE
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

@router.get("/content/coverage")
async def get_content_coverage(db: AsyncSession = Depends(get_db)):
    """Get content coverage across all chapters"""
    
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
    
    coverage_report = []
    
    for chapter in chapters:
        # Get content count for this chapter
        result = await db.execute(
            select(func.count()).select_from(ContentCurriculumMapping)
            .where(ContentCurriculumMapping.curriculum_node_id == chapter.id)
        )
        total_count = result.scalar()
        
        # Get counts by type
        result = await db.execute(
            select(Content.content_type, func.count())
            .join(ContentCurriculumMapping)
            .where(ContentCurriculumMapping.curriculum_node_id == chapter.id)
            .group_by(Content.content_type)
        )
        by_type = {row[0]: row[1] for row in result}
        
        # Calculate coverage score (target: 20 resources per chapter)
        score = min(100, int((total_count / 20) * 100))
        
        # Determine status
        status = "excellent" if score >= 80 else "good" if score >= 60 else "needs_attention"
        
        coverage_report.append({
            "chapter_code": chapter.code,
            "chapter_name": chapter.name,
            "chapter_number": chapter.order_num,
            "total_resources": total_count,
            "by_type": by_type,
            "coverage_score": score,
            "status": status,
            "needs_attention": status == "needs_attention"
        })
    
    # Summary
    total_resources = sum(c["total_resources"] for c in coverage_report)
    poor_chapters = [c for c in coverage_report if c["status"] == "needs_attention"]
    
    return {
        "summary": {
            "total_chapters": len(chapters),
            "total_resources": total_resources,
            "chapters_needing_attention": len(poor_chapters)
        },
        "coverage": coverage_report,
        "needs_attention": poor_chapters
    }


# ============================================================================
# PROCESSING QUEUE
# ============================================================================

@router.get("/processing/queue")
async def get_processing_queue(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """View pending processing tasks"""
    
    query = select(ProcessingQueue)
    
    if status:
        query = query.where(ProcessingQueue.status == status)
    
    query = query.order_by(ProcessingQueue.priority.desc(), ProcessingQueue.created_at).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return {
        "total": len(tasks),
        "tasks": [
            {
                "id": str(task.id),
                "content_id": str(task.content_id),
                "task_type": task.task_type,
                "status": task.status,
                "priority": task.priority,
                "progress": task.progress,
                "attempts": task.attempts,
                "created_at": task.created_at.isoformat()
            }
            for task in tasks
        ]
    }


# ============================================================================
# PAST PAPERS - LIST FOR STUDENTS
# ============================================================================

@router.get("/past-papers/list")
async def list_past_papers(
    year: Optional[int] = None,
    province: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all past papers (public endpoint for students)"""
    
    query = select(Content).where(
        Content.content_type == "past_paper",
        Content.processing_status == "completed"
    )
    query = query.order_by(Content.created_at.desc())
    
    result = await db.execute(query)
    papers = result.scalars().all()
    
    papers_list = []
    for p in papers:
        metadata = p.content_metadata if p.content_metadata else {}
        exam_info = metadata.get("exam", {}) if isinstance(metadata, dict) else {}
        
        paper_year = exam_info.get("year")
        paper_province = exam_info.get("province")
        
        if year and paper_year != year:
            continue
        if province and paper_province != province:
            continue
        
        papers_list.append({
            "id": str(p.id),
            "title": p.title,
            "year": paper_year,
            "province": paper_province,
            "full_marks": exam_info.get("full_marks", 75),
            "file_path": p.file_path,
            "file_size": p.file_size,
            "page_count": p.page_count or 0,
            "download_url": f"/api/v1/admin/content/download/{p.id}",
            "created_at": p.created_at.isoformat()
        })
    
    return {"total": len(papers_list), "papers": papers_list}


# ============================================================================
# PAST PAPERS - FILTERS (Years & Provinces)
# ============================================================================

@router.get("/past-papers/filters")
async def get_past_paper_filters(db: AsyncSession = Depends(get_db)):
    """Get available years and provinces for filtering"""
    
    result = await db.execute(
        select(Content).where(
            Content.content_type == "past_paper",
            Content.processing_status == "completed"
        )
    )
    papers = result.scalars().all()
    
    years = set()
    provinces = set()
    
    for p in papers:
        metadata = p.content_metadata if p.content_metadata else {}
        exam_info = metadata.get("exam", {}) if isinstance(metadata, dict) else {}
        
        if exam_info.get("year"):
            years.add(exam_info["year"])
        if exam_info.get("province"):
            provinces.add(exam_info["province"])
    
    return {
        "years": sorted(list(years), reverse=True),
        "provinces": sorted(list(provinces))
    }


# ============================================================================
# ADMIN - GET PAST PAPERS (with processing status)
# ============================================================================

@router.get("/past-papers/admin-list")
async def admin_list_past_papers(db: AsyncSession = Depends(get_db)):
    """List all past papers for admin view"""
    
    result = await db.execute(
        select(Content)
        .where(Content.content_type == "past_paper")
        .order_by(Content.created_at.desc())
    )
    papers = result.scalars().all()
    
    papers_list = []
    for p in papers:
        metadata = p.content_metadata if p.content_metadata else {}
        exam_info = metadata.get("exam", {}) if isinstance(metadata, dict) else {}
        
        papers_list.append({
            "id": str(p.id),
            "title": p.title,
            "year": exam_info.get("year"),
            "province": exam_info.get("province"),
            "processing_status": p.processing_status,
            "chunks_count": p.chunks_count or 0,
            "page_count": p.page_count or 0,
            "file_size": p.file_size,
            "created_at": p.created_at.isoformat()
        })
    
    return {"total": len(papers_list), "papers": papers_list}


# ============================================================================
# CONTENT DOWNLOAD
# ============================================================================

@router.get("/content/download/{content_id}")
async def download_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Download content file (PDF)"""
    try:
        # Convert string to UUID
        content_uuid = uuid.UUID(content_id)
        
        result = await db.execute(
            select(Content).where(Content.id == content_uuid)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Check if file exists
        file_path = Path(content.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {content.file_path}")
        
        # Increment download count
        content.downloads += 1
        await db.commit()
        
        # Return file
        return FileResponse(
            path=str(file_path),
            filename=f"{content.title}.pdf",
            media_type="application/pdf"
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID format")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Download error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTENT VIEW (Serve PDF for inline viewing)
# ============================================================================

@router.get("/content/view/{content_id}")
async def view_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """View content file inline (for PDF viewer)"""
    try:
        # Convert string to UUID
        content_uuid = uuid.UUID(content_id)
        
        result = await db.execute(
            select(Content).where(Content.id == content_uuid)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        file_path = Path(content.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Increment view count
        content.views += 1
        await db.commit()
        
        # Return file for inline viewing
        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{content.title}.pdf"'
            }
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ View error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))