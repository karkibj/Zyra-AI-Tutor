// Progress API Service - For Progress Tracking Dashboard
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Helper to get auth headers
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token');
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
}

// Types
export interface TopicProgress {
  topic: string;
  chapter_code: string | null;
  total_questions_attempted: number;
  correct_answers: number;
  mastery_percentage: number;
  mastery_level: 'beginner' | 'learning' | 'improving' | 'mastered';
  status_emoji: string;
  last_practiced_at: string | null;
}

export interface OverallStats {
  overall_mastery: number;
  total_questions: number;
  correct_answers: number;
  total_topics_studied: number;
  mastered_topics: number;
}

export interface RecentActivity {
  today: number;
  this_week: number;
  this_month: number;
  week_accuracy: number;
}

export interface DashboardData {
  overall_stats: OverallStats;
  topic_progress: TopicProgress[];
  weak_areas: TopicProgress[];
  recent_activity: RecentActivity;
}

export const progressApi = {
  /**
   * Get complete dashboard data
   */
  async getDashboard(): Promise<DashboardData> {
    try {
      const response = await fetch(`${API_BASE_URL}/progress/dashboard`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      throw error;
    }
  },

  /**
   * Get topic-wise progress breakdown
   */
  async getTopics(): Promise<TopicProgress[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/progress/topics`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.topics || [];
    } catch (error) {
      console.error('Error fetching topics:', error);
      throw error;
    }
  },

  /**
   * Get weak areas (topics below mastery threshold)
   */
  async getWeakAreas(threshold: number = 50): Promise<TopicProgress[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/progress/weak-areas?threshold=${threshold}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.weak_areas || [];
    } catch (error) {
      console.error('Error fetching weak areas:', error);
      throw error;
    }
  },

  /**
   * Get recent activity stats
   */
  async getActivity(days: number = 30): Promise<RecentActivity> {
    try {
      const response = await fetch(`${API_BASE_URL}/progress/activity?days=${days}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching activity:', error);
      throw error;
    }
  },

  /**
   * Get overall stats only
   */
  async getOverallStats(): Promise<OverallStats> {
    try {
      const response = await fetch(`${API_BASE_URL}/progress/overall`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching overall stats:', error);
      throw error;
    }
  },

  /**
   * Health check for progress tracking system
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/progress/health`);
      const data = await response.json();
      return data.status === 'healthy';
    } catch (error) {
      console.error('Progress health check failed:', error);
      return false;
    }
  },
};