"""
LangGraph Agent Nodes
Each function is an agent that processes state
"""
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents.state import AgentState
from app.core.llm import get_llm
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store
from app.rag.intent_classifier import IntentClassifier, Intent


# Initialize services
intent_classifier = IntentClassifier()
embedding_service = get_embedding_service()
vector_store = get_vector_store()
llm = get_llm(temperature=0.3)


def intent_router_node(state: AgentState) -> AgentState:
    """
    Route based on intent classification
    Determines which agents to activate
    """
    state.agent_path.append("intent_router")
    
    # Classify intent
    intent = intent_classifier.classify(state.question)
    state.intent = intent.value
    
    # Set flags
    state.is_greeting = intent in [Intent.GREETING, Intent.FEEDBACK]
    state.is_math_question = intent == Intent.MATHEMATICAL_QUERY
    state.is_practice_request = "practice" in state.question.lower() or "question" in state.question.lower()
    
    return state


def retriever_node(state: AgentState) -> AgentState:
    """Retrieve relevant context from vector store"""
    state.agent_path.append("retriever")
    
    print(f"🔍 RETRIEVER NODE:")
    print(f"   Question: {state.question}")
    
    if not state.is_math_question:
        return state
    
    # Generate embedding
    query_embedding = embedding_service.generate_embedding(state.question)
    print(f"   ✅ Generated query embedding: shape {query_embedding.shape}")
    
    # Detect content type filter
    question_lower = state.question.lower()
    requested_type = None
    
    if any(kw in question_lower for kw in [
        'model question', 'model paper', 'practice question', 
        'sample question', 'see question', 'exam question'
    ]):
        requested_type = 'model_question'
        print(f"   🎯 User requested: model_question")
    elif any(kw in question_lower for kw in [
        'past paper', 'previous paper', 'province paper'
    ]):
        requested_type = 'past_paper'
        print(f"   🎯 User requested: past_paper")
    
    # ✅ KEY FIX: When filtering by type, search MORE results
    # Because model_question vectors might not be in top 20 by similarity
    if requested_type:
        # Search up to 100 results to find the filtered type
        search_k = 100
    else:
        search_k = 4
    
    results = vector_store.search(
        query_vector=query_embedding,
        k=search_k,
        filters=None
    )
    
    print(f"   📊 Initial search returned {len(results)} results")
    
    # Filter by content type if requested
    if requested_type:
        filtered_results = [
            r for r in results 
            if r.get('content_type') == requested_type
        ]
        print(f"   🔍 After filtering for '{requested_type}': {len(filtered_results)} results")
        
        # Take top 4 of the filtered results
        results = filtered_results[:4]
        
        if results:
            print(f"   ✅ Found {len(results)} {requested_type} results:")
            for i, r in enumerate(results, 1):
                title = r.get('title', 'N/A')
                score = r.get('score', 0)
                print(f"      {i}. Score: {score:.3f}, Title: {title}")
        else:
            print(f"   ⚠️  No {requested_type} results found!")
    else:
        # No filtering, just take top 4
        results = results[:4]
        if results:
            for i, r in enumerate(results, 1):
                title = r.get('title', 'N/A')
                content_type = r.get('content_type', 'N/A')
                score = r.get('score', 0)
                print(f"      {i}. Type: {content_type}, Score: {score:.3f}")
    
    # Convert to state format
    from app.agents.state import RetrievedContext
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
    
    print(f"   ✅ Final: {len(state.retrieved_contexts)} contexts\n")
    
    return state

def curriculum_agent_node(state: AgentState) -> AgentState:
    """
    Check curriculum context and prerequisites
    Provides educational context
    """
    state.agent_path.append("curriculum_agent")
    
    if not state.is_math_question or not state.retrieved_contexts:
        return state
    
    # Build curriculum context from retrieved docs
    chapters = set()
    topics = []
    
    for ctx in state.retrieved_contexts:
        if ctx.chapter:
            chapters.add(ctx.chapter)
        topics.append(ctx.title)
    
    state.curriculum_check = {
        "related_chapters": list(chapters),
        "related_topics": topics[:3],
        "context_available": len(state.retrieved_contexts) > 0
    }
    
    return state


def tutor_agent_node(state: AgentState) -> AgentState:
    """
    Main teaching agent - explains concepts clearly with conversation context
    """
    state.agent_path.append("tutor_agent")
    
    if not state.is_math_question or not state.retrieved_contexts:
        # Handle greetings or no context
        # Even here, check if there's conversation history
        if state.conversation_history:
            # Build conversation context
            conv_lines = []
            for msg in state.conversation_history[-6:]:
                role = "Student" if msg.role == "user" else "Zyra"
                conv_lines.append(f"{role}: {msg.content}")
            conversation_context = "\n".join(conv_lines)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are Zyra, a friendly math tutor for Grade 10 students in Nepal.
                You are helpful, encouraging, and explain things clearly.
                Remember the conversation history to provide contextual responses."""),
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
            # No conversation history
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are Zyra, a friendly math tutor for Grade 10 students in Nepal.
                You are helpful, encouraging, and explain things clearly."""),
                ("user", "{question}")
            ])
            
            chain = prompt | llm | StrOutputParser()
            state.explanation = chain.invoke({"question": state.question})
        
        return state
    
    # Build context from retrieved documents
    context_text = "\n\n".join([
        f"[From {ctx.title}]:\n{ctx.text}"
        for ctx in state.retrieved_contexts
    ])
    
    # Build conversation history for context awareness
    conversation_context = ""
    if state.conversation_history:
        conv_lines = []
        for msg in state.conversation_history[-6:]:  # Last 3 exchanges (6 messages)
            role = "Student" if msg.role == "user" else "Zyra"
            conv_lines.append(f"{role}: {msg.content}")
        conversation_context = "\n".join(conv_lines)
    
    # Create teaching prompt WITH conversation history
    if conversation_context:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Zyra, an expert mathematics tutor for Grade 10 CDC students in Nepal.

Your teaching style:
- Explain concepts step-by-step
- Use clear, simple language
- Break down complex ideas
- Show the "why" behind formulas
- Be encouraging and supportive
- Remember previous parts of the conversation to understand follow-up questions

Guidelines:
- Use ONLY information from the provided context
- If context doesn't have enough info, say so honestly
- Explain in a way a Grade 10 student can understand
- Use proper mathematical notation when needed
- Pay attention to the conversation history to provide relevant answers
- If the student says "give me an example" or "explain more", refer to what was just discussed
"""),
            ("user", """Previous Conversation:
{conversation_history}

Context from CDC Textbook:
{context}

Current Question: {question}

Provide a clear, step-by-step explanation that builds on our conversation:""")
        ])
        
        chain = prompt | llm | StrOutputParser()
        
        state.explanation = chain.invoke({
            "conversation_history": conversation_context,
            "context": context_text,
            "question": state.question
        })
    else:
        # No conversation history (first message)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Zyra, an expert mathematics tutor for Grade 10 CDC students in Nepal.

Your teaching style:
- Explain concepts step-by-step
- Use clear, simple language
- Break down complex ideas
- Show the "why" behind formulas
- Be encouraging and supportive

Guidelines:
- Use ONLY information from the provided context
- If context doesn't have enough info, say so honestly
- Explain in a way a Grade 10 student can understand
- Use proper mathematical notation when needed
"""),
            ("user", """Context from CDC Textbook:
{context}

Student Question: {question}

Provide a clear, step-by-step explanation:""")
        ])
        
        chain = prompt | llm | StrOutputParser()
        
        state.explanation = chain.invoke({
            "context": context_text,
            "question": state.question
        })
    
    return state


def example_agent_node(state: AgentState) -> AgentState:
    """
    Provides worked examples when helpful
    """
    state.agent_path.append("example_agent")
    
    # Only provide examples for math questions with good context
    if not state.is_math_question or not state.retrieved_contexts or len(state.retrieved_contexts) < 2:
        return state
    
    # Check if question seems to need examples
    needs_example = any(word in state.question.lower() for word in ['example', 'solve', 'calculate', 'how to'])
    
    if not needs_example:
        return state
    
    # Generate example
    context_text = "\n\n".join([ctx.text for ctx in state.retrieved_contexts[:2]])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a math teacher providing worked examples for Grade 10 students."),
        ("user", """Based on this content:
{context}

Provide ONE simple worked example that demonstrates the concept for: {question}

Keep it brief and clear.""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    example = chain.invoke({
        "context": context_text,
        "question": state.question
    })
    
    state.examples.append(example)
    
    return state


def practice_suggester_node(state: AgentState) -> AgentState:
    """
    Suggests practice questions after explanation
    """
    state.agent_path.append("practice_suggester")
    
    # Only suggest practice for successful explanations
    if not state.explanation or state.is_greeting:
        return state
    
    # Simple suggestion (later we'll make this generate actual questions)
    state.practice_questions = [
        {
            "suggestion": "Would you like me to generate practice questions on this topic?",
            "can_generate": True
        }
    ]
    
    return state


def response_compiler_node(state: AgentState) -> AgentState:
    """
    Compile final response from all agent outputs
    """
    state.agent_path.append("response_compiler")
    
    parts = []
    
    # Add main explanation
    if state.explanation:
        parts.append(state.explanation)
    
    # Add examples if available
    if state.examples:
        parts.append("\n\n**Example:**")
        parts.extend(state.examples)
    
    # Add practice suggestion
    if state.practice_questions and not state.is_greeting:
        parts.append("\n\n💡 Want to practice? I can generate questions for you!")
    
    state.final_answer = "\n".join(parts)
    
    # Prepare sources
    state.sources = [
        {
            "content_id": ctx.content_id,
            "title": ctx.title,
            "score": ctx.score,
            "chapter": ctx.chapter
        }
        for ctx in state.retrieved_contexts
    ]
    
    return state