"""
LangGraph Agent Nodes - IMPROVED VERSION
Fixes: LaTeX formatting, language detection, topic badge, example agent discipline
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents.state import AgentState
from app.core.llm import get_llm, rotate_current_key
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store
from app.rag.intent_classifier import IntentClassifier, Intent
from app.agents.state import RetrievedContext
from app.core.logging import logger


# Initialize services (no LLM at module level — instantiated per-call for key rotation)
intent_classifier = IntentClassifier()
embedding_service = get_embedding_service()
vector_store = get_vector_store()


# ── Chapter keyword map for topic detection from question text ────────────────
CHAPTER_QUESTION_KEYWORDS = {
    "Sets":                        ["set", "venn", "union", "intersection", "cardinality", "n(a", "subset", "complement"],
    "Compound Interest":           ["compound interest", "ci", "half yearly", "semi-annual", "principal", "compounded"],
    "Growth and Depreciation":     ["growth", "depreciation", "population growth", "rate of growth"],
    "Currency and Exchange Rate":  ["currency", "exchange rate", "dollar", "rupees", "conversion", "devaluation"],
    "Area and Volume":             ["area", "volume", "surface area", "cylinder", "cone", "sphere", "pyramid", "prism", "frustum", "hemisphere"],
    "Sequence and Series":         ["sequence", "series", "arithmetic progression", "tn", "sn", "t_n", "s_n", "common difference", "nth term"],
    "Quadratic Equation":          ["quadratic", "quadratic equation", "roots", "discriminant", "factori"],
    "Algebraic Fraction":          ["algebraic fraction", "simplify", "rational expression"],
    "Indices":                     ["indices", "index", "exponent", "laws of indices", "a^"],
    "Triangles and Quadrilaterals":["triangle", "quadrilateral", "parallel", "congruent", "similar", "area of triangle"],
    "Construction":                ["construction", "construct", "perpendicular bisector", "angle bisector"],
    "Circle":                      ["circle", "chord", "tangent", "arc", "cyclic", "inscribed angle", "radius"],
    "Statistics":                  ["statistics", "mean", "median", "mode", "quartile", "frequency table", "continuous series", "q1", "q3"],
    "Probability":                 ["probability", "p(e)", "sample space", "tree diagram", "favorable", "at least"],
    "Trigonometry":                ["trigonometry", "sin", "cos", "tan", "angle of elevation", "angle of depression", "height and distance"],
}

CHAPTER_CODES = {
    "Sets": "CDC-10-MATH-CH01",
    "Compound Interest": "CDC-10-MATH-CH02",
    "Growth and Depreciation": "CDC-10-MATH-CH03",
    "Currency and Exchange Rate": "CDC-10-MATH-CH04",
    "Area and Volume": "CDC-10-MATH-CH05",
    "Sequence and Series": "CDC-10-MATH-CH06",
    "Quadratic Equation": "CDC-10-MATH-CH07",
    "Algebraic Fraction": "CDC-10-MATH-CH08",
    "Indices": "CDC-10-MATH-CH09",
    "Triangles and Quadrilaterals": "CDC-10-MATH-CH10",
    "Construction": "CDC-10-MATH-CH11",
    "Circle": "CDC-10-MATH-CH12",
    "Statistics": "CDC-10-MATH-CH13",
    "Probability": "CDC-10-MATH-CH14",
    "Trigonometry": "CDC-10-MATH-CH15",
}


# ── Chapter-enhanced query prefixes for better semantic matching ─────────────
# Defined at module level to avoid recreation on every retriever call
CHAPTER_PREFIXES = {
    "statistics":          "Statistics mean median mode quartile frequency table continuous series",
    "probability":         "Probability sample space event tree diagram favorable outcomes",
    "sequence":            "Arithmetic sequence series Tn Sn common difference first term progression",
    "series":              "Arithmetic sequence series Tn Sn common difference first term",
    "sets":                "Sets cardinality n(A) n(B) n(AuB) n(AnB) survey Venn diagram cardinal number formula",
    "compound interest":   "Compound interest principal rate time formula half-yearly",
    "growth":              "Growth depreciation population rate formula",
    "quadratic":           "Quadratic equation factorization formula discriminant roots",
    "trigonometry":        "Trigonometry sin cos tan angle elevation depression height distance",
    "circle":              "Circle chord tangent arc inscribed angle cyclic quadrilateral theorem",
    "triangle":            "Triangle quadrilateral congruent similar parallel area proof",
    "mensuration":         "Area volume surface area prism cylinder cone sphere pyramid",
    "area":                "Area volume surface area prism cylinder cone sphere pyramid",
    "indices":             "Indices exponent laws power a^m a^n base",
    "algebraic fraction":  "Algebraic fraction simplify rational expression LCM",
}


def detect_topic_from_question(question: str) -> tuple[str | None, str | None]:
    """Detect chapter directly from question text — more reliable than context metadata."""
    q = question.lower()
    scores = {}
    for chapter, keywords in CHAPTER_QUESTION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[chapter] = score
    if not scores:
        return None, None
    best = max(scores, key=scores.get)
    return best, CHAPTER_CODES.get(best, "")


def detect_language(question: str) -> str:
    """Detect if student wants English or Nepali response."""
    q = question.lower()
    english_signals = [
        "in english", "english ma", "english mा", "english me",
        "explain in english", "tell me in english"
    ]
    # If question is mostly ASCII (English words), respond in English
    ascii_ratio = sum(1 for c in question if ord(c) < 128) / max(len(question), 1)
    if any(sig in q for sig in english_signals) or ascii_ratio > 0.85:
        return "english"
    return "nepali"


def intent_router_node(state: AgentState) -> AgentState:
    """Route based on intent classification"""
    state.agent_path.append("intent_router")

    intent = intent_classifier.classify(state.question)
    state.intent = intent.value

    state.is_greeting = intent in [Intent.GREETING, Intent.FEEDBACK]
    state.is_math_question = intent == Intent.MATHEMATICAL_QUERY
    state.is_practice_request = (
        "practice" in state.question.lower() or
        "question" in state.question.lower()
    )

    return state


def retriever_node(state: AgentState) -> AgentState:
    """Retrieve relevant context — enhanced with chapter-aware query"""
    state.agent_path.append("retriever")

    logger.info(f"[RETRIEVER] {state.question}")

    if not state.is_math_question:
        return state

    # ── Chapter-enhanced query for better semantic matching ──────────────────
    q_lower = state.question.lower()
    enhanced_query = state.question
    for keyword, prefix in CHAPTER_PREFIXES.items():
        if keyword in q_lower:
            enhanced_query = f"{prefix} {state.question}"
            break

    enhanced_embedding = embedding_service.generate_embedding(enhanced_query)

    # Detect content type filter
    requested_type = None
    if any(kw in q_lower for kw in ['model question', 'model paper', 'practice question', 'sample question', 'see question', 'exam question', 'like model', 'see exam', 'see style', 'exam style', 'neb question']):
        requested_type = 'model_question'
    elif any(kw in q_lower for kw in ['past paper', 'previous paper', 'province paper']):
        requested_type = 'past_paper'

    search_k = 8  # Always 8 — direct lookup handles model/past paper

    results = vector_store.search(
        query_vector=enhanced_embedding,
        k=search_k,
        filters=None
    )

    # Filter by content type if requested
    if requested_type:
        # Direct metadata lookup — no embedding search needed.
        # Model/past paper chunks are few and tagged — filter directly.
        all_meta = vector_store.metadata_list
        filtered = [m for m in all_meta if m.get('content_type') == requested_type]
        
        # Narrow by chapter if detectable from question or conversation
        detected_for_filter, _ = detect_topic_from_question(state.question)
        
        # If question alone has no chapter, check conversation history
        if not detected_for_filter and state.conversation_history:
            for msg in reversed(state.conversation_history[-6:]):
                topic, _ = detect_topic_from_question(msg.content)
                if topic:
                    detected_for_filter = topic
                    break

        if detected_for_filter:
            chapter_filtered = [m for m in filtered if m.get('chapter') == detected_for_filter]
            results = chapter_filtered[:4] if chapter_filtered else filtered[:4]
        else:
            results = filtered[:4]
        
        logger.info(f"Direct lookup: {len(filtered)} {requested_type} chunks, {len(results)} selected")
    else:
        # Prefer chapter-tagged results + always include a model question example
        detected_chapter, _ = detect_topic_from_question(state.question)
        if detected_chapter:
            # Curriculum chunks for this chapter
            curriculum_results = [r for r in results
                                  if r.get('chapter') == detected_chapter
                                  and r.get('content_type') == 'curriculum']
            # Model question chunks for this chapter
            model_q_results = [r for r in results
                               if r.get('chapter') == detected_chapter
                               and r.get('content_type') == 'model_question']
            # Other results as fallback
            other_results = [r for r in results
                             if r.get('chapter') != detected_chapter]
            # Mix: 2 curriculum + 1 model question + 1 other
            results = (curriculum_results[:2] + model_q_results[:1] + other_results)[:4]
        else:
            results = results[:4]

    state.retrieved_contexts = [
        RetrievedContext(
            text=r.get('text', ''),
            content_id=r.get('content_id', ''),
            title=r.get('title', 'Unknown'),
            score=r.get('score', 0.0),
            chapter=r.get('chapter')
        )
        for r in results
    ]

    logger.info(f"Retrieved {len(state.retrieved_contexts)} contexts")
    for ctx in state.retrieved_contexts:
        logger.info(f"  chapter='{ctx.chapter}' score={ctx.score:.3f} title='{ctx.title}'")

    return state


def curriculum_agent_node(state: AgentState) -> AgentState:
    """Extract curriculum metadata — use question-based detection for accuracy"""
    state.agent_path.append("curriculum_agent")

    if not state.is_math_question:
        return state

    chapters = set()
    topics   = []

    for ctx in state.retrieved_contexts:
        if ctx.chapter:
            chapters.add(ctx.chapter)
        topics.append(ctx.title)

    # ── Detect topic from question itself — more reliable ────────────────────
    detected_topic, detected_code = detect_topic_from_question(state.question)

    # Use detected topic as primary; fall back to retrieved context chapters
    if detected_topic:
        primary_chapter = detected_topic
    elif chapters:
        primary_chapter = list(chapters)[0]
    else:
        primary_chapter = None

    state.curriculum_check = {
        "related_chapters":  list(chapters),
        "related_topics":    topics[:3],
        "context_available": len(state.retrieved_contexts) > 0,
        "detected_topic":    primary_chapter,   # ← used by frontend for badge
        "detected_code":     detected_code or "",
    }

    return state





async def tutor_agent_node(state: AgentState) -> AgentState:
    """Main teaching agent — LaTeX formatting + language detection"""
    state.agent_path.append("tutor_agent")
    # Get LLM — rotate key if previous was rate limited
    llm = get_llm(temperature=0.3)
    LANGUAGE_RULE = """
LANGUAGE RULE (HIGHEST PRIORITY):
- If the student's question is in English or contains "in english" → respond ENTIRELY in English
- If the student's question is in Nepali → respond in Nepali
- NEVER mix languages within a single explanation
- Match exactly what the student is using"""

    MATH_FORMAT_RULE = """
MATH FORMATTING (CRITICAL — ALWAYS FOLLOW):
- ALWAYS wrap ALL mathematical expressions in LaTeX delimiters
- Inline math: $expression$  e.g. $x^2 + 5x + 6 = 0$
- Block/display math: $$expression$$  e.g. $$M = L + \\frac{{\\frac{{N}}{{2}} - cf}}{{f}} \\times i$$
- Examples:
  Variables: $x$, $y$, $n$
  Equations: $3x + 7 = 22$
  Fractions: $\\frac{{a}}{{b}}$
  Powers: $x^2$, $2^n$
  Square roots: $\\sqrt{{16}} = 4$
  Summation: $\\sum fx$, $\\bar{{x}} = \\frac{{\\sum fx}}{{\\sum f}}$
  Median: $$M = L + \\frac{{\\frac{{N}}{{2}} - cf}}{{f}} \\times i$$
  Mode: $$Mo = L + \\frac{{f_1 - f_0}}{{2f_1 - f_0 - f_2}} \\times i$$
  Quartile: $$Q_1 = L + \\frac{{\\frac{{N}}{{4}} - cf}}{{f}} \\times i$$
  CI: $$A = P\\left(1 + \\frac{{R}}{{100}}\\right)^T$$
  Quadratic: $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}{{2a}}$$
- NEVER write math as plain text like: x^2 or N/2 or Sn = n/2[...]"""

    TOPIC_RULE = """
TOPIC DISCIPLINE (CRITICAL):
- ONLY explain the specific topic the student asked about
- Do NOT mix in examples or content from other chapters
- If context contains mixed chapters, extract ONLY what is relevant

SEE EXAM ALIGNMENT (CRITICAL):
- Always teach at SEE Grade 10 level — not basic/elementary level
- For SETS: Focus on cardinality problems, n(AuB) = n(A) + n(B) - n(AnB), survey problems with Venn diagrams. NOT just element listing.
- For STATISTICS: Focus on Mean/Median/Mode from frequency tables, quartiles. NOT just definitions.
- For PROBABILITY: Focus on P(E) = n(E)/n(S), tree diagrams, real-life scenarios.
- Always use SEE exam-style word problems (survey of people, real scenarios) not abstract math.

DIAGRAM RULE (IMPORTANT):
- Do NOT draw ASCII art diagrams or text-based figures (e.g. using | \ / + characters)
- Do NOT say "here's how it would look conceptually" and draw ASCII
- A proper SVG diagram will be automatically added after your response
- Just describe the concept in text — the visual will be handled separately"""

    # ── Adaptive difficulty based on student mastery ─────────────────────────
    detected_topic_for_mastery, _ = detect_topic_from_question(state.question)
    mastery_pct = 0.0
    if detected_topic_for_mastery and state.user_id:
        mastery_pct = await _get_student_mastery(state.user_id, detected_topic_for_mastery)
    difficulty_label, difficulty_instruction = _get_adaptive_difficulty(mastery_pct)
    logger.info(f"Adaptive difficulty: {difficulty_label} ({mastery_pct:.0f}% mastery on {detected_topic_for_mastery})")

    TEACHING_STYLE = f"""
TEACHING STYLE:
✓ Maximum 400 words total
✓ Use numbered steps (Step 1, Step 2, Step 3)
✓ ONE concrete worked example with LaTeX math — use SEE exam style (survey/real-life context)
✓ For Sets: use cardinality problems with n(A), n(B), n(AuB), n(AnB) — NOT just element listing
✓ For Sets: always include the formula n(AuB) = n(A) + n(B) - n(AnB)
✓ {difficulty_instruction}
✓ Be encouraging and supportive"""

    # ── Handle greetings / no math context ──────────────────────────────────
    if not state.is_math_question or not state.retrieved_contexts:
        if state.conversation_history:
            conv_lines = []
            for msg in state.conversation_history[-6:]:
                role = "Student" if msg.role == "user" else "Zyra"
                conv_lines.append(f"{role}: {msg.content}")
            conversation_context = "\n".join(conv_lines)

            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are Zyra, a friendly Grade 10 math tutor in Nepal.
Be helpful, encouraging, and remember our conversation context.
{LANGUAGE_RULE}
{MATH_FORMAT_RULE}"""),
                ("user", """Previous conversation:
{conversation_history}

Current question: {question}""")
            ])
            chain = prompt | llm | StrOutputParser()
            state.explanation = chain.invoke({
                "conversation_history": conversation_context,
                "question": state.question
            })
        else:
            # Fresh session — greet with student's progress awareness
            student_profile = ""
            if state.user_id:
                student_profile = await _get_student_profile(state.user_id)

            if student_profile:
                # Returning student — personalised greeting
                prompt = ChatPromptTemplate.from_messages([
                    ("system", f"""You are Zyra, a friendly Grade 10 math tutor in Nepal.
You know this student's learning history. Use it naturally in your response.
{LANGUAGE_RULE}
{MATH_FORMAT_RULE}

Student's learning history: {student_profile}

GREETING RULES:
- Greet them warmly, mention what they last studied or their weak area
- Suggest they continue or ask what they need help with today
- Keep greeting to 2-3 sentences — don't overwhelm
- Match the student's language (English or Nepali)"""),
                    ("user", "{question}")
                ])
            else:
                # New student — standard greeting
                prompt = ChatPromptTemplate.from_messages([
                    ("system", f"""You are Zyra, a friendly Grade 10 math tutor in Nepal.
Be helpful and encouraging.
{LANGUAGE_RULE}
{MATH_FORMAT_RULE}"""),
                    ("user", "{question}")
                ])

            chain = prompt | llm | StrOutputParser()
            state.explanation = chain.invoke({"question": state.question})

        return state

    # ── Build context ────────────────────────────────────────────────────────
    context_text = "\n\n".join([
        f"[From {ctx.title} — Chapter: {ctx.chapter or 'General'}]:\n{ctx.text}"
        for ctx in state.retrieved_contexts
    ])

    # ── Conversation history ─────────────────────────────────────────────────
    conversation_context = ""
    if state.conversation_history:
        conv_lines = []
        for msg in state.conversation_history[-6:]:
            role = "Student" if msg.role == "user" else "Zyra"
            conv_lines.append(f"{role}: {msg.content}")
        conversation_context = "\n".join(conv_lines)

    # ── Model questions special prompt ───────────────────────────────────────
    has_model_questions = any('model' in ctx.title.lower() for ctx in state.retrieved_contexts)
    is_practice_request = state.is_practice_request or any(
        kw in state.question.lower() for kw in ['practice', 'questions from']
    )

    if has_model_questions and is_practice_request:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Zyra, showing SEE model questions to students.
CRITICAL INSTRUCTIONS:
- Extract ONLY English text (ignore garbled Devanagari like clgjfo{{ ul0ft)
- Show EXACT questions from the papers
- Format: Question number, text, marks [1], [2], [3]
- DO NOT generate your own questions
- Present in clean, numbered format
- Use LaTeX for all math: $x^2$, $$formula$$"""),
            ("user", """Model Papers Context:
{context}

Student Request: {question}

Show actual questions (English only):""")
        ])
        chain = prompt | llm | StrOutputParser()
        try:
            state.explanation = chain.invoke({
                "context": context_text,
                "question": state.question
            })
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                logger.warning("429 rate limit on main chain — rotating key and retrying")
                llm2 = rotate_current_key()
                chain2 = prompt | llm2 | StrOutputParser()
                state.explanation = chain2.invoke({
                    "context": context_text,
                    "question": state.question
                })
            else:
                raise
        await _log_chat_interaction(state)
        return state

    # ── Main teaching prompt ─────────────────────────────────────────────────
    system_prompt = f"""You are Zyra, an expert Grade 10 math tutor for CDC students in Nepal.

{LANGUAGE_RULE}

{MATH_FORMAT_RULE}

{TOPIC_RULE}

{TEACHING_STYLE}

RULES:
- Use ONLY the provided context relevant to the question topic
- Keep under 400 words
- If context lacks info, say so honestly
- Reference previous conversation when relevant"""

    if conversation_context:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", """Previous Conversation:
{conversation_history}

CDC Curriculum Context:
{context}

Student Question: {question}

Teach concisely with LaTeX math and one worked example:""")
        ])
        chain = prompt | llm | StrOutputParser()
        try:
            state.explanation = chain.invoke({
                "conversation_history": conversation_context,
                "context": context_text,
                "question": state.question
            })
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                logger.warning("429 rate limit on conv chain — rotating key and retrying")
                llm2 = rotate_current_key()
                chain2 = prompt | llm2 | StrOutputParser()
                state.explanation = chain2.invoke({
                    "conversation_history": conversation_context,
                    "context": context_text,
                    "question": state.question
                })
            else:
                raise
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", """CDC Curriculum Context:
{context}

Student Question: {question}

Teach concisely with LaTeX math and one worked example:""")
        ])
        chain = prompt | llm | StrOutputParser()
        try:
            state.explanation = chain.invoke({
                "context": context_text,
                "question": state.question
            })
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                logger.warning("429 rate limit on main chain — rotating key and retrying")
                llm2 = rotate_current_key()
                chain2 = prompt | llm2 | StrOutputParser()
                state.explanation = chain2.invoke({
                    "context": context_text,
                    "question": state.question
                })
            else:
                raise

    await _log_chat_interaction(state)
    # Solution view is handled lazily via /tutor/solution endpoint
    # No extra LLM call here — keeps responses fast
    return state


async def _log_chat_interaction(state: AgentState):
    """Log chat interactions to progress tracking"""
    try:
        if not state.user_id:
            return

        from app.services.progress_service import ProgressTrackingService
        from app.db import get_db_session

        # Use question-based detection for accurate topic logging
        detected_topic, detected_code = detect_topic_from_question(state.question)

        topic = detected_topic
        chapter_code = detected_code

        # Fall back to context metadata if question detection failed
        if not topic and state.retrieved_contexts:
            first_ctx = state.retrieved_contexts[0]
            topic = first_ctx.chapter or first_ctx.title
            chapter_code = first_ctx.chapter

        async with get_db_session() as db:
            service = ProgressTrackingService(db)
            await service.log_interaction(
                user_id=state.user_id,
                interaction_type="chat_question",
                topic=topic,
                chapter_code=chapter_code,
                question_text=state.question,
                user_answer=None,
                is_correct=None,
                time_spent_seconds=None
            )
            logger.info(f"Interaction logged: topic='{topic}' code='{chapter_code}'")

    except Exception as e:
        logger.warning(f"Failed to log interaction: {e}")



async def _get_student_mastery(user_id: str, topic: str) -> float:
    """
    Read student mastery % for a topic from DB.
    Returns 0.0 if no data found (new topic).
    Used for adaptive difficulty in practice questions.
    """
    try:
        if not user_id or not topic:
            return 0.0
        from app.db import get_db_session
        from app.models.progress import TopicMastery
        from sqlalchemy import select
        async with get_db_session() as db:
            result = await db.execute(
                select(TopicMastery).where(
                    TopicMastery.user_id == user_id,
                    TopicMastery.topic == topic
                )
            )
            mastery = result.scalar_one_or_none()
            return mastery.mastery_percentage if mastery else 0.0
    except Exception as e:
        logger.warning(f"Could not fetch mastery: {e}")
        return 0.0


def _get_adaptive_difficulty(mastery_pct: float) -> tuple[str, str]:
    """
    Rule-based adaptive difficulty.
    Returns (difficulty_label, practice_instruction) based on mastery %.

    Rules:
      0%        → Beginner  → Easy: basic definition/formula question
      1–30%     → Beginner  → Easy: simple single-step calculation
      31–60%    → Learning  → Medium: standard SEE-style word problem
      61–80%    → Improving → Hard: multi-step problem
      81–100%   → Mastered  → Challenge: exam-level complex problem
    """
    if mastery_pct == 0:
        return "beginner", (
            "End with an EASY practice question — basic formula or definition level. "
            "Student is new to this topic."
        )
    elif mastery_pct <= 30:
        return "easy", (
            "End with an EASY practice question — single-step calculation. "
            f"Student mastery is {mastery_pct:.0f}% (beginner)."
        )
    elif mastery_pct <= 60:
        return "medium", (
            "End with a MEDIUM practice question — standard SEE exam style word problem. "
            f"Student mastery is {mastery_pct:.0f}% (learning)."
        )
    elif mastery_pct <= 80:
        return "hard", (
            "End with a HARD practice question — multi-step problem requiring combined concepts. "
            f"Student mastery is {mastery_pct:.0f}% (improving)."
        )
    else:
        return "challenge", (
            "End with a CHALLENGE question — exam-level complex problem. "
            f"Student mastery is {mastery_pct:.0f}% (mastered). Push them further!"
        )



async def _get_student_profile(user_id: str) -> str:
    """
    Build a brief student profile from topic_mastery for greeting awareness.
    Returns empty string if no data (new student).
    Only called on fresh session greeting — not on every message.
    """
    try:
        if not user_id:
            return ""
        from app.db import get_db_session
        from app.models.progress import TopicMastery
        from sqlalchemy import select
        async with get_db_session() as db:
            result = await db.execute(
                select(TopicMastery)
                .where(TopicMastery.user_id == user_id)
                .order_by(TopicMastery.last_practiced_at.desc())
            )
            masteries = result.scalars().all()

            if not masteries:
                return ""

            # Build profile summary
            lines = []

            # Most recently practiced
            recent = masteries[0]
            lines.append(f"Last studied: {recent.topic} ({recent.mastery_percentage:.0f}% mastery)")

            # Weak areas (mastery < 50%)
            weak = [m for m in masteries if m.mastery_percentage < 50 and m.total_questions_attempted > 0]
            if weak:
                weak_names = ", ".join(m.topic for m in weak[:2])
                lines.append(f"Needs practice: {weak_names}")

            # Strong areas (mastery >= 75%)
            strong = [m for m in masteries if m.mastery_percentage >= 75]
            if strong:
                strong_names = ", ".join(m.topic for m in strong[:2])
                lines.append(f"Mastered: {strong_names}")

            return " | ".join(lines)

    except Exception as e:
        logger.warning(f"Could not fetch student profile: {e}")
        return ""


def example_agent_node(state: AgentState) -> AgentState:
    """Provides worked examples — strictly on the same topic as the question"""
    state.agent_path.append("example_agent")
    llm = get_llm(temperature=0.3)  # Fresh key per call

    if not state.is_math_question or not state.retrieved_contexts or len(state.retrieved_contexts) < 2:
        return state

    # Check English and Nepali trigger words
    example_triggers_en = ['example', 'solve', 'calculate', 'how to', 'show me', 'show', 'demonstrate', 'देखाउनुहोस्']
    example_triggers_np = ['देखाउनुहोस्', 'उदाहरण', 'सिकाउनुहोस्', 'बुझाउनुहोस्', 'गर्नुहोस्']
    needs_example = (
        any(w in state.question.lower() for w in example_triggers_en) or
        any(w in state.question for w in example_triggers_np)
    )

    if not needs_example:
        return state

    # Get detected topic for strict topic discipline
    detected_topic, _ = detect_topic_from_question(state.question)
    topic_instruction = f"The example MUST be about '{detected_topic}'." if detected_topic else ""

    context_text = "\n\n".join([ctx.text for ctx in state.retrieved_contexts[:2]])

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a math teacher providing ONE worked example.

STRICT RULES:
- {topic_instruction}
- Do NOT use examples from other chapters
- Use LaTeX: $...$ for inline math, $$...$$ for block math
- Brief (100-150 words max), clear step-by-step
- ONE example only"""),
        ("user", """Student's question: {question}

Curriculum context (use ONLY relevant parts):
{context}

Provide ONE brief worked example STRICTLY about the topic in the question:""")
    ])

    chain = prompt | llm | StrOutputParser()
    example = chain.invoke({
        "context": context_text,
        "question": state.question
    })

    state.examples.append(example)
    return state


def practice_suggester_node(state: AgentState) -> AgentState:
    """Practice suggestions are handled naturally by the tutor prompt.
    Node kept in workflow for compatibility."""
    state.agent_path.append("practice_suggester")
    return state


def response_compiler_node(state: AgentState) -> AgentState:
    """Compile final response"""
    state.agent_path.append("response_compiler")

    parts = []

    if state.explanation:
        parts.append(state.explanation)

    if state.examples:
        parts.append("\n\n**Example:**")
        parts.extend(state.examples)

    # Practice suggestion removed — Zyra naturally ends responses
    # with "Try this: [question]" from the teaching prompt itself

    state.final_answer = "\n".join(parts)

    # Append SVG visualization if generated
    if state.visualization_svg:
        state.final_answer += f"\n\n:::svg\n{state.visualization_svg}\n:::"

    # Prepare sources with chapter info
    state.sources = [
        {
            "content_id": ctx.content_id,
            "title":      ctx.title,
            "score":      ctx.score,
            "chapter":    ctx.chapter
        }
        for ctx in state.retrieved_contexts
    ]

    return state