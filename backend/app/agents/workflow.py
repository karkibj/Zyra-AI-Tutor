"""
LangGraph Workflow Definition
Orchestrates agents to create intelligent tutoring
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


def should_retrieve(state: AgentState) -> str:
    """Decide if we need to retrieve context"""
    # TEMPORARY: Force retrieval for ALL questions to test
    # This will help us verify the vector store is working
    
    # Skip retrieval only for pure greetings
    if state.is_greeting and len(state.question.split()) <= 3:
        # Very short greetings like "hi", "hello", "thanks"
        return "tutor"
    
    # Retrieve for everything else (including follow-ups)
    return "retrieve"


def should_add_example(state: AgentState) -> str:
    """Decide if we should add examples"""
    if state.is_math_question and len(state.retrieved_contexts) >= 2:
        return "example"
    else:
        return "practice_suggester"


def build_tutor_workflow() -> StateGraph:
    """
    Build the complete tutoring workflow
    
    Flow:
    1. Intent Router → Classify question
    2. Retriever → Get relevant context (if needed)
    3. Curriculum Agent → Check educational context
    4. Tutor Agent → Explain concept
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
    workflow.add_node("tutor", tutor_agent_node)
    workflow.add_node("example", example_agent_node)
    workflow.add_node("practice_suggester", practice_suggester_node)
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
    workflow.add_edge("practice_suggester", "compile")
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