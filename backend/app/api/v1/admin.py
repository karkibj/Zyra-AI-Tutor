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
                    print(f" Chapter not found: {code}")
            except Exception as mapping_error:
                print(f" Error mapping {code}: {mapping_error}")
        
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
                "chunks_count": c.chunks_count or 0,
                "page_count": c.page_count or 0,
                "file_size": c.file_size or 0,
                "created_at": c.created_at.isoformat()
            }
            for c in content_list
        ]
    }




@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a content item, its curriculum mappings,
    AND its vectors from the FAISS knowledge base.
    """
    try:
        result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content_item = result.scalar_one_or_none()

        if not content_item:
            raise HTTPException(status_code=404, detail="Content not found")

        content_title = content_item.title

        # Step 1 — Remove vectors from FAISS knowledge base
        vectors_removed = 0
        try:
            import pickle
            import faiss
            import numpy as np
            from pathlib import Path

            meta_file = Path("data/vector_store/metadata.pkl")
            index_paths = [
                Path("data/vector_store/faiss.index"),
                Path("data/vector_store/index.faiss")
            ]
            index_path = next((p for p in index_paths if p.exists()), None)

            if meta_file.exists() and index_path:
                with open(meta_file, 'rb') as f:
                    all_metadata = pickle.load(f)

                # Separate chunks to keep vs remove
                keep_meta = [m for m in all_metadata
                             if m.get('content_id') != content_id]
                vectors_removed = len(all_metadata) - len(keep_meta)

                if vectors_removed > 0:
                    # Rebuild FAISS without this content's vectors
                    old_index = faiss.read_index(str(index_path))
                    dim = old_index.d
                    new_index = faiss.IndexFlatL2(dim)
                    new_metadata = []

                    for meta in keep_meta:
                        vid = meta.get('vector_id')
                        if vid is not None and vid < old_index.ntotal:
                            vec = old_index.reconstruct(int(vid))
                            new_meta = dict(meta)
                            new_meta['vector_id'] = len(new_metadata)
                            new_metadata.append(new_meta)
                            new_index.add(
                                np.array([vec], dtype='float32')
                            )

                    # Save updated index and metadata
                    faiss.write_index(new_index, str(index_path))
                    with open(meta_file, 'wb') as f:
                        pickle.dump(new_metadata, f)

                    print(f"[OK] Removed {vectors_removed} vectors for: {content_title}")

        except Exception as vec_err:
            # Log but don't fail — DB cleanup still proceeds
            print(f"[WARN] Vector cleanup partial: {vec_err}")

        # Step 2 — Delete curriculum mappings from DB
        mappings_result = await db.execute(
            select(ContentCurriculumMapping).where(
                ContentCurriculumMapping.content_id == content_item.id
            )
        )
        for mapping in mappings_result.scalars().all():
            await db.delete(mapping)

        # Step 3 — Delete content record from DB
        await db.delete(content_item)
        await db.commit()

        return {
            "status": "deleted",
            "id": content_id,
            "title": content_title,
            "vectors_removed": vectors_removed
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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

@router.get("/knowledge-base/stats")
async def get_knowledge_base_stats():
    """Get real-time knowledge base statistics from the vector store."""
    try:
        import pickle
        from pathlib import Path
        from collections import Counter
        from app.services.vector_store_service import get_vector_store

        vs = get_vector_store()
        basic_stats = vs.get_stats()

        metadata_file = Path("data/vector_store/metadata.pkl")
        if not metadata_file.exists():
            return {"error": "Vector store not found", "total_vectors": 0}

        with open(metadata_file, "rb") as f:
            metadata = pickle.load(f)

        type_counts = Counter(m.get("content_type", "unknown") for m in metadata)
        chapter_counts = Counter(
            m.get("chapter", "Untagged")
            for m in metadata
            if m.get("content_type") == "curriculum"
        )

        # SEE marks per chapter (from test specification grid 2078)
        # Stored here as single source of truth until exam_specifications table is populated
        SEE_MARKS_BY_CODE = {
            "CDC-10-MATH-CH01": 6,  "CDC-10-MATH-CH02": 5,
            "CDC-10-MATH-CH03": 4,  "CDC-10-MATH-CH04": 4,
            "CDC-10-MATH-CH05": 8,  "CDC-10-MATH-CH06": 5,
            "CDC-10-MATH-CH07": 5,  "CDC-10-MATH-CH08": 5,
            "CDC-10-MATH-CH09": 5,  "CDC-10-MATH-CH10": 5,
            "CDC-10-MATH-CH11": 4,  "CDC-10-MATH-CH12": 4,
            "CDC-10-MATH-CH13": 6,  "CDC-10-MATH-CH14": 5,
            "CDC-10-MATH-CH15": 4,
        }

        # Get chapter names and codes from DB — single source of truth
        from app.models.curriculum import CurriculumNode
        from app.db import get_db_session
        async with get_db_session() as db_session:
            ch_result = await db_session.execute(
                select(CurriculumNode)
                .where(CurriculumNode.code.like("CDC-10-MATH-CH%"))
                .where(CurriculumNode.active == True)
                .order_by(CurriculumNode.order_num)
            )
            db_chapters = ch_result.scalars().all()

        chapters = []
        for ch in db_chapters:
            count = chapter_counts.get(ch.name, 0)
            health = "good" if count >= 30 else "moderate" if count >= 10 else "low"
            chapters.append({
                "name": ch.name,
                "code": ch.code,
                "see_marks": SEE_MARKS_BY_CODE.get(ch.code, 0),
                "chunk_count": count,
                "health": health,
            })

        garbled = sum(
            1 for m in metadata
            if m.get("content_type") == "model_question" and not m.get("chapter")
        )
        total_tagged = sum(1 for m in metadata if m.get("chapter"))

        return {
            "total_vectors": basic_stats["total_vectors"],
            "total_tagged": total_tagged,
            "total_untagged": basic_stats["total_vectors"] - total_tagged,
            "by_content_type": dict(type_counts),
            "chapters": chapters,
            "garbled_chunks": garbled,
            "index_size_mb": round(basic_stats.get("index_file_size", 0) / 1024 / 1024, 1),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "total_vectors": 0}

@router.get("/users/list")
async def list_users(db: AsyncSession = Depends(get_db)):
    """List all registered users with activity stats."""
    try:
        from app.models.user import User
        from app.models.chat import ChatConversation
        from app.models.progress import TopicMastery
        from sqlalchemy import func

        result = await db.execute(
            select(User).order_by(User.created_at.desc())
        )
        users = result.scalars().all()

        user_list = []
        for u in users:
            # Chat count
            chat_result = await db.execute(
                select(func.count(ChatConversation.id)).where(
                    ChatConversation.user_id == u.id
                )
            )
            chat_count = chat_result.scalar() or 0

            # Topics practiced
            mastery_result = await db.execute(
                select(func.count(TopicMastery.id)).where(
                    TopicMastery.user_id == u.id
                )
            )
            topics_count = mastery_result.scalar() or 0

            user_list.append({
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name or "Unknown",
                "role": u.role,
                "provider": u.provider,
                "is_active": u.is_active,
                "chat_count": chat_count,
                "topics_practiced": topics_count,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            })

        return {
            "total": len(user_list),
            "students": len([u for u in user_list if u["role"] == "student"]),
            "admins": len([u for u in user_list if u["role"] == "admin"]),
            "users": user_list
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))