"""
LangGraph Workflow Definition
Orchestrates agents to create intelligent tutoring + Progress Tracking
"""

from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import (
    intent_router_node,
    retriever_node,
    curriculum_agent_node,
    tutor_agent_node,  
    example_agent_node,
    practice_suggester_node,
    response_compiler_node
)
from app.agents.visualization_agent import visualization_agent_node

def should_retrieve(state: AgentState) -> str:
    """Decide if retrieval is needed.
    Short greetings skip retrieval and go straight to the tutor node.
    Everything else — including follow-up questions — goes through retrieval.
    """
    if state.is_greeting and len(state.question.split()) <= 3:
        return "tutor"
    return "retrieve"


def should_add_example(state: AgentState) -> str:
    """Decide if we should add examples — only when student explicitly asks"""
    
    if not state.is_math_question or len(state.retrieved_contexts) < 2:
        return "practice_suggester"
    
    # Only add example if student explicitly asked for one
    # Avoids duplicate examples when tutor already gave a worked example
    q = state.question.lower()
    explicit_example_request = any(w in q for w in [
        'example', 'उदाहरण', 'देखाउनुहोस्', 'show me', 'demonstrate',
        'solve this', 'work out', 'step by step'
    ])
    
    # If explanation already contains a worked example, skip
    explanation = state.explanation or ""
    already_has_example = any(phrase in explanation.lower() for phrase in [
        "worked example", "example:", "let's solve", "step 1:", "step 2:"
    ])
    
    if explicit_example_request and not already_has_example:
        return "example"
    
    return "practice_suggester"


def build_tutor_workflow() -> StateGraph:
    """
    Build the complete tutoring workflow
    
    Flow:
    1. Intent Router → Classify question
    2. Retriever → Get relevant context (if needed)
    3. Curriculum Agent → Check educational context
    4. Tutor Agent → Explain concept ( NOW ASYNC - logs progress)
    5. Example Agent → Provide worked example (if helpful)
    6. Practice Suggester → Offer practice questions
    7. Response Compiler → Build final answer
    """
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("retrieve", retriever_node)
    workflow.add_node("curriculum", curriculum_agent_node)
    workflow.add_node("tutor", tutor_agent_node)  #  LangGraph handles async automatically
    workflow.add_node("example", example_agent_node)
    workflow.add_node("practice_suggester", practice_suggester_node)
    workflow.add_node("visualization", visualization_agent_node)
    workflow.add_node("compile", response_compiler_node)
    
    # Set entry point
    workflow.set_entry_point("intent_router")
    
    # Define edges (workflow flow)
    workflow.add_conditional_edges(
        "intent_router",
        should_retrieve,
        {
            "retrieve": "retrieve",
            "tutor": "tutor"
        }
    )
    
    workflow.add_edge("retrieve", "curriculum")
    workflow.add_edge("curriculum", "tutor")
    
    workflow.add_conditional_edges(
        "tutor",
        should_add_example,
        {
            "example": "example",
            "practice_suggester": "practice_suggester"
        }
    )
    
    workflow.add_edge("example", "practice_suggester")
    workflow.add_edge("practice_suggester", "visualization")
    workflow.add_edge("visualization", "compile")
    workflow.add_edge("compile", END)
    
    return workflow.compile()


# Global workflow instance
_workflow = None

def get_tutor_workflow():
    """Get compiled workflow instance"""
    global _workflow
    if _workflow is None:
        _workflow = build_tutor_workflow()
    return _workflow