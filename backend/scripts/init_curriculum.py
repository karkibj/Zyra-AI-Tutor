"""
Initialize CDC Grade 10 Mathematics Curriculum Structure
Run this ONCE to populate the curriculum_nodes table
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.curriculum import CurriculumNode
from sqlalchemy import select


async def init_curriculum():
    """Initialize CDC Grade 10 Mathematics curriculum structure"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if already initialized
            result = await db.execute(select(CurriculumNode).where(CurriculumNode.code == "CDC"))
            if result.scalar_one_or_none():
                print("⚠️  Curriculum already initialized!")
                return
            
            print("🚀 Initializing CDC Grade 10 Mathematics Curriculum...")
            
            # 1. Create CDC Board
            cdc = CurriculumNode(
                code="CDC",
                node_type="board",
                name="Curriculum Development Centre",
                order_num=1,
                active=True
            )
            db.add(cdc)
            await db.flush()  # Get the ID
            print("✅ Created: CDC Board")
            
            # 2. Create Grade 10
            grade10 = CurriculumNode(
                code="CDC-10",
                node_type="grade",
                name="Grade 10",
                parent_id=cdc.id,
                order_num=10,
                active=True
            )
            db.add(grade10)
            await db.flush()
            print("✅ Created: Grade 10")
            
            # 3. Create Mathematics Subject
            math = CurriculumNode(
                code="CDC-10-MATH",
                node_type="subject",
                name="Mathematics",
                parent_id=grade10.id,
                order_num=1,
                active=True,
                metadata={
                    "total_marks": 75,
                    "duration_minutes": 180,
                    "total_chapters": 14
                }
            )
            db.add(math)
            await db.flush()
            print("✅ Created: Mathematics")
            
            # 4. Create ALL 14 Chapters (CDC Official)
            chapters = [
                ("CDC-10-MATH-CH01", "Sets", 1, {"pages": "1-25", "unit": "Sets & Logic"}),
                ("CDC-10-MATH-CH02", "Compound Interest", 2, {"pages": "26-46", "unit": "Financial Mathematics"}),
                ("CDC-10-MATH-CH03", "Growth and Depreciation", 3, {"pages": "47-65", "unit": "Financial Mathematics"}),
                ("CDC-10-MATH-CH04", "Currency and Exchange Rate", 4, {"pages": "66-79", "unit": "Financial Mathematics"}),
                ("CDC-10-MATH-CH05", "Area and Volume", 5, {"pages": "80-129", "unit": "Mensuration"}),
                ("CDC-10-MATH-CH06", "Sequence and Series", 6, {"pages": "130-151", "unit": "Algebra"}),
                ("CDC-10-MATH-CH07", "Quadratic Equation", 7, {"pages": "152-172", "unit": "Algebra"}),
                ("CDC-10-MATH-CH08", "Algebraic Fraction", 8, {"pages": "173-180", "unit": "Algebra"}),
                ("CDC-10-MATH-CH09", "Indices", 9, {"pages": "181-193", "unit": "Algebra"}),
                ("CDC-10-MATH-CH10", "Triangles and Quadrilaterals", 10, {"pages": "194-209", "unit": "Geometry"}),
                ("CDC-10-MATH-CH11", "Construction", 11, {"pages": "210-220", "unit": "Geometry"}),
                ("CDC-10-MATH-CH12", "Circle", 12, {"pages": "221-238", "unit": "Geometry"}),
                ("CDC-10-MATH-CH13", "Statistics", 13, {"pages": "239-270", "unit": "Statistics & Probability"}),
                ("CDC-10-MATH-CH14", "Probability", 14, {"pages": "271-293", "unit": "Statistics & Probability"}),
            ]
            
            for code, name, order, metadata in chapters:
                chapter = CurriculumNode(
                    code=code,
                    node_type="chapter",
                    name=name,
                    parent_id=math.id,
                    order_num=order,
                    active=True,
                    metadata=metadata
                )
                db.add(chapter)
                print(f"✅ Created: Chapter {order:02d} - {name}")
            
            # Commit all changes
            await db.commit()
            
            print("\n🎉 SUCCESS! Curriculum structure initialized!")
            print(f"📊 Created: 1 Board, 1 Grade, 1 Subject, 14 Chapters")
            
        except Exception as e:
            await db.rollback()
            print(f"\n ERROR: {e}")
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("CDC GRADE 10 MATHEMATICS CURRICULUM INITIALIZATION")
    print("=" * 60)
    asyncio.run(init_curriculum())