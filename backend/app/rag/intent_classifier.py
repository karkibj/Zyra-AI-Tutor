from enum import Enum
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.llm import get_llm
from app.core.prompts import INTENT_CLASSIFIER_PROMPT


class Intent(str, Enum):
    GREETING = "GREETING"
    CLARIFICATION = "CLARIFICATION"
    MATHEMATICAL_QUERY = "MATHEMATICAL_QUERY"
    OFF_TOPIC = "OFF_TOPIC"
    FEEDBACK = "FEEDBACK"


class IntentClassifier:
    """Classifies user intent — lazy LLM init to support key rotation."""

    def __init__(self):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_CLASSIFIER_PROMPT),
            ("human", "{user_message}")
        ])
        # Don't build chain at init — build fresh per call for key rotation

    def classify(self, user_message: str) -> Intent:
        """Classify user intent."""
        try:
            # Build chain fresh each call — picks best available API key
            llm = get_llm(temperature=0.1)
            chain = self.prompt | llm | StrOutputParser()
            result = chain.invoke({"user_message": user_message})
            result_clean = result.strip().upper()

            for intent in Intent:
                if intent.value in result_clean:
                    return intent

            return Intent.MATHEMATICAL_QUERY

        except Exception as e:
            print(f"Intent classification error: {e}")
            return Intent.MATHEMATICAL_QUERY