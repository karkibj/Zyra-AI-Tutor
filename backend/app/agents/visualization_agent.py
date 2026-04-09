"""
Visualization Agent for Zyra AI Tutor
Generates SVG diagrams for mathematical concepts using Gemini.

Handles:
- Venn diagrams (Sets)
- Right-angled triangles (Trigonometry)
- 3D shapes as 2D diagrams (Mensuration)
- Tree diagrams (Probability)
- Circle theorems (Circle)
- Coordinate planes
- Frequency tables
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.agents.state import AgentState
from app.core.llm import get_llm
from app.core.logging import logger
import re

def needs_visualization(question: str, explanation: str = "") -> tuple[bool, str]:
    q = question.lower()

    venn_keywords = ["venn", "venn diagram", "draw a set", "show sets",
                     "set diagram", "union diagram", "intersection diagram",
                     "visualize set", "visually explain set", "visual set",
                     "venn को", "venn diagram देखाउ"]
    if any(w in q for w in venn_keywords):
        return True, "venn"

    is_visual_request = any(w in q for w in [
        "visualize", "visually", "visual explain",
        "explain visually", "चित्रमा", "diagram", "draw", "show me"
    ])

    if is_visual_request:
        if any(w in q for w in ["set", "union", "intersection", "venn"]):
            return True, "venn"
        if any(w in q for w in ["triangle", "angle", "sin", "cos", "tan", "trigonometry"]):
            return True, "triangle"
        if any(w in q for w in ["cone", "cylinder", "sphere", "pyramid", "prism"]):
            return True, "shapes"
        if any(w in q for w in ["circle", "chord", "tangent", "arc"]):
            return True, "circle"
        if any(w in q for w in ["probability", "tree", "outcome"]):
            return True, "tree"

    triangle_keywords = [
        "draw a triangle", "show a triangle", "right-angled triangle",
        "angle of elevation diagram", "angle of depression diagram",
        "soh cah toa diagram", "trigonometry diagram"
    ]
    if any(w in q for w in triangle_keywords):
        return True, "triangle"

    shapes_explicit = [
        "draw a cone", "show a cone", "draw a cylinder", "show a cylinder",
        "draw a sphere", "show a sphere", "draw a pyramid", "show a pyramid",
        "draw a hemisphere", "show a hemisphere", "draw a prism",
        "diagram of cone", "diagram of cylinder", "diagram of sphere",
        "sketch a cone", "sketch a cylinder", "sketch a pyramid",
        "visualize cone", "visualize cylinder", "visualize pyramid",
        "visualize hemisphere", "visualize sphere", "visualize prism",
        "सोलीको चित्र", "वेलनाको चित्र", "गोलाको चित्र"
    ]
    if any(w in q for w in shapes_explicit):
        return True, "shapes"

    if is_visual_request and any(w in q for w in [
        "cone", "cylinder", "sphere", "hemisphere", "pyramid", "prism"
    ]):
        return True, "shapes"

    circle_keywords = [
        "draw a circle", "show a circle", "circle diagram",
        "circle theorem diagram", "show chord", "show tangent"
    ]
    if any(w in q for w in circle_keywords):
        return True, "circle"

    tree_keywords = [
        "tree diagram", "draw tree", "show tree", "probability tree"
    ]
    if any(w in q for w in tree_keywords):
        return True, "tree"

    coord_keywords = [
        "plot", "draw the graph", "show the graph",
        "graph of y =", "graph of f(x)", "coordinate plane"
    ]
    if any(w in q for w in coord_keywords):
        return True, "coordinate"

    table_keywords = [
        "draw a table", "show a table", "frequency table"
    ]
    if any(w in q for w in table_keywords):
        return True, "table"

    return False, ""


SVG_SYSTEM_PROMPT = """You are a mathematical diagram generator for a Grade 10 Nepal CDC tutor.
Generate clean, educational SVG diagrams.

STRICT SVG RULES:
- Output ONLY the SVG element
- Start with <svg and end with </svg>
- viewBox="0 0 400 300"
- Use clean colors and labels
- All text in English
- Keep it simple and educational
"""


VISUAL_PROMPTS = {
    "shapes": """Draw a clear labeled educational SVG diagram for this 3D shape problem:
{question}

Draw as a 2D projection.

SHAPE RULES:
- CONE: triangle + ellipse base, label r, h, l
- CYLINDER: rectangle + ellipses, label r, h
- SPHERE: circle center O, label r
- PYRAMID: triangle + base, label h, l, b

Always:
- dashed hidden lines
- arrows for labels
- clean textbook style
- White background, viewBox="0 0 400 320"
""",

    "venn": """Draw a Venn diagram SVG for:
{question}""",

    "triangle": """Draw a right triangle SVG for:
{question}""",

    "circle": """Draw a circle diagram SVG for:
{question}""",

    "tree": """Draw a probability tree diagram SVG for:
{question}""",

    "coordinate": """Draw coordinate plane SVG for:
{question}""",

    "table": """Draw frequency table SVG for:
{question}""",

    "general": """Draw a math diagram SVG for:
{question}"""
}


def extract_svg(text: str) -> str | None:
    match = re.search(r'<svg[\s\S]*?</svg>', text, re.IGNORECASE)
    return match.group(0) if match else None


def visualization_agent_node(state: AgentState) -> AgentState:
    state.agent_path.append("visualization_agent")

    if not state.is_math_question:
        return state

    should_visualize, visual_type = needs_visualization(
        state.question,
        state.explanation or ""
    )

    if not should_visualize:
        return state

    state.needs_visualization = True
    logger.info(f"Visualization triggered: {visual_type}")

    try:
        llm = get_llm(temperature=0.1)

        user_template = VISUAL_PROMPTS.get(
            visual_type,
            VISUAL_PROMPTS["general"]
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", SVG_SYSTEM_PROMPT),
            ("user", user_template)
        ])

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"question": state.question})

        svg = extract_svg(result)

        if svg:
            state.visualization_svg = svg
            logger.info("SVG generated successfully")
        else:
            logger.warning("No SVG found in LLM response")

    except Exception as e:
        logger.error(f"Visualization error: {e}")

    return state