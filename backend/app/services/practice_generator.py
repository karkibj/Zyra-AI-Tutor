"""
Practice Question Generator
Generates practice questions with varying difficulty levels using the LLM.
"""
from typing import List, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

from app.core.llm import get_llm
from app.core.logging import logger


class PracticeQuestionGenerator:
    """Generates and checks practice questions via the LLM."""

    def generate_questions(
        self,
        topic: str,
        difficulty: str = "medium",
        count: int = 5,
        curriculum_context: Optional[str] = None,
    ) -> List[Dict]:
        """
        Generate practice questions for a given topic and difficulty.

        Args:
            topic:               Math topic (e.g. "Probability", "Quadratic Equation")
            difficulty:          "easy" | "medium" | "hard"
            count:               Number of questions to generate
            curriculum_context:  Optional CDC curriculum text for grounding

        Returns:
            List of question dicts containing question, answer, hints,
            difficulty, marks, id, and topic.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert mathematics question creator for the Grade 10 CDC curriculum in Nepal.

Generate practice questions that:
- Match the CDC Grade 10 syllabus exactly
- Are appropriate for SEE exam preparation
- Have clear, specific answers with brief explanations
- Include step-by-step hints (subtle → direct → near-answer)
- Follow official SEE exam question patterns

Difficulty levels:
- Easy:   Basic definitions, single-step calculations (1–2 marks)
- Medium: Multi-step problems, concept application (2–3 marks)
- Hard:   Complex scenarios combining multiple concepts (3+ marks)

Return ONLY valid JSON in this exact format — no markdown, no code blocks:
{{
  "questions": [
    {{
      "question": "Question text",
      "answer":   "Correct answer with brief explanation",
      "hints": [
        "First hint (subtle)",
        "Second hint (more direct)",
        "Third hint (nearly gives it away)"
      ],
      "difficulty": "easy|medium|hard",
      "marks": 1
    }}
  ]
}}"""),
            ("user", """Topic: {topic}
Difficulty: {difficulty}
Number of questions: {count}

{context_section}

Generate {count} practice questions as JSON:"""),
        ])

        context_section = (
            f"CDC Curriculum & Past Paper Context:\n{curriculum_context}\n\n"
            "Base your questions on this curriculum content and past paper patterns."
            if curriculum_context
            else "Generate questions based on the standard Grade 10 CDC curriculum."
        )

        # Fresh LLM per call for API key rotation; higher temperature for variety
        chain = prompt | get_llm(temperature=0.7) | StrOutputParser()

        response = chain.invoke({
            "topic":           topic,
            "difficulty":      difficulty,
            "count":           count,
            "context_section": context_section,
        })

        try:
            data      = json.loads(_clean_json(response))
            questions = data.get("questions", [])

            for i, q in enumerate(questions, 1):
                q["id"]    = i
                q["topic"] = topic

            return questions

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in generate_questions: {e} | response={response!r}")
            return []

    def check_answer(self, user_answer: str, correct_answer: str) -> Dict:
        """
        Use the LLM to evaluate whether a student's answer is correct,
        accepting mathematically equivalent forms (e.g. 0.5 = 1/2 = 50%).

        Returns:
            Dict with keys: is_correct (bool), feedback (str)
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly SEE Mathematics tutor giving feedback directly to a Grade 10 student.

Evaluate whether the student's answer is correct and respond encouragingly.
Accept mathematically equivalent forms (e.g. 0.5 = 1/2 = 50%, x = -3 = -3.0).

Feedback rules:
- Speak directly to the student using "you" — never say "the student"
- If correct: acknowledge clearly and briefly reinforce the concept
- If incorrect: be kind, point out specifically what went wrong, and give a nudge toward the right approach
- Keep feedback to 1–2 sentences — concise and encouraging
- Do not reveal the full correct answer in feedback

Return ONLY valid JSON — no markdown, no extra text:
{{
  "is_correct": true,
  "feedback": "Great work! You correctly applied the formula and simplified the expression."
}}"""),
            ("user", """Your Answer: {user_answer}
Correct Answer: {correct_answer}

Evaluate and return JSON:"""),
        ])

        # Low temperature for consistent, deterministic evaluation
        chain = prompt | get_llm(temperature=0.1) | StrOutputParser()

        response = chain.invoke({
            "user_answer":    user_answer,
            "correct_answer": correct_answer,
        })

        try:
            return json.loads(_clean_json(response))

        except json.JSONDecodeError:
            # Fallback: simple string containment check
            is_correct = user_answer.lower().strip() in correct_answer.lower()
            return {
                "is_correct": is_correct,
                "feedback": (
                    "Correct! Well done."
                    if is_correct
                    else "Not quite right. Review the hints or ask Zyra for help."
                ),
            }


def _clean_json(raw: str) -> str:
    """Strip markdown code fences from an LLM response, returning raw JSON."""
    text = raw.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        text = text.split("\n", 1)[-1]
        # Remove closing fence
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


# ── Singleton ─────────────────────────────────────────────────────────────────

_practice_generator: Optional[PracticeQuestionGenerator] = None


def get_practice_generator() -> PracticeQuestionGenerator:
    """Return the shared PracticeQuestionGenerator instance."""
    global _practice_generator
    if _practice_generator is None:
        _practice_generator = PracticeQuestionGenerator()
    return _practice_generator