// API Service - Enhanced for LangGraph Backend with Auth Support
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface TutorQueryRequest {
  question: string;        // Changed from 'query' to match new backend
  chapter_code?: string;   // Changed from 'chapter' to match new backend
  session_id?: string;     // Added session support
}

// Updated to match LangGraph backend response
export interface TutorQueryResponse {
  answer: string;
  intent: string;
  sources: Array<{         // NEW - sources from vector store
    content_id: string;
    title: string;
    score: number;
    chapter?: string;
  }>;
  session_id: string;      // NEW - session tracking
  chunk_count: number;
  response_time: number;
  timestamp: string;
  metadata?: {
    agent_path: string[];
    curriculum_check?: any;
    examples_provided: number;
    practice_offered: boolean;
  };
}

export interface ConversationHistory {
  messages: Array<{
    role: string;
    content: string;
  }>;
}

// ✅ NEW: Helper to get auth headers
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token');
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  // Add Authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
}

export const tutorApi = {
  /**
   * Ask Zyra a question using LangGraph multi-agent workflow
   */
  async askQuestion(
    question: string, 
    chapterCode?: string,
    sessionId?: string
  ): Promise<TutorQueryResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/tutor/ask`, {
        method: 'POST',
        headers: getAuthHeaders(),  // ✅ FIXED: Now includes auth token
        body: JSON.stringify({
          question,
          chapter_code: chapterCode,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data: TutorQueryResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Error calling tutor API:', error);
      throw error;
    }
  },

  /**
   * Get conversation history for a session
   */
  async getConversationHistory(sessionId: string): Promise<ConversationHistory> {
    try {
      const response = await fetch(`${API_BASE_URL}/tutor/conversation/${sessionId}`, {
        headers: getAuthHeaders(),  // ✅ ADDED: Auth for this endpoint too
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting conversation history:', error);
      throw error;
    }
  },

  /**
   * Check if backend is healthy and ready
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/tutor/health`);
      const data = await response.json();
      return data.status === 'healthy';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  },

  /**
   * Get RAG system statistics
   */
  async getStats(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/tutor/stats`);
      return await response.json();
    } catch (error) {
      console.error('Failed to get stats:', error);
      return null;
    }
  },
};

// ── Lazy solution fetcher — called only when student clicks "Solution Only" ───
export interface SolutionResponse {
  solution: string;
  has_solution: boolean;
}

export async function fetchSolution(
  question: string,
  answer: string,
  topic?: string
): Promise<SolutionResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/tutor/solution`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ question, answer, topic }),
    });
    if (!res.ok) return { solution: '', has_solution: false };
    return await res.json();
  } catch {
    return { solution: '', has_solution: false };
  }
}