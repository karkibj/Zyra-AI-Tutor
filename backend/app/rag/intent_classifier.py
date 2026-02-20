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
    """Classifies user intent to route to appropriate handler."""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.1)  # Low temperature for consistent classification
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_CLASSIFIER_PROMPT),
            ("human", "{user_message}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def classify(self, user_message: str) -> Intent:
        """
        Classify user intent.
        
        Args:
            user_message: The user's input message
            
        Returns:
            Intent enum value
        """
        try:
            result = self.chain.invoke({"user_message": user_message})
            result_clean = result.strip().upper()
            
            # Try to match to Intent enum
            for intent in Intent:
                if intent.value in result_clean:
                    return intent
            #to fix
            # Default to MATHEMATICAL_QUERY if unclear
            return Intent.MATHEMATICAL_QUERY
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            # Default to MATHEMATICAL_QUERY on error
            return Intent.MATHEMATICAL_QUERY
        

        