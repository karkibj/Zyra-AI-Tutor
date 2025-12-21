const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface TutorQueryRequest {
  query: string;
  chapter?: string;
}

export interface TutorQueryResponse {
  reply: string;
}

export const tutorApi = {
  async askQuestion(query: string, chapter: string = 'money_exchange'): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/tutor/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          chapter,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: TutorQueryResponse = await response.json();
      return data.reply;
    } catch (error) {
      console.error('Error calling tutor API:', error);
      throw error;
    }
  },

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      const data = await response.json();
      return data.status === 'ok';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  },
};