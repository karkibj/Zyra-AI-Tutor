// Admin API Service - Enhanced for Phase 4
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// ==================== INTERFACES ====================

export interface SystemStats {
  total_documents: number;
  total_chunks: number;
  total_embeddings: number;
  status: string;
  chapters: Record<string, number>;
  recent_uploads: DocumentInfo[];
}

export interface DocumentInfo {
  document_id: string;
  title: string;
  chapter: string;
  file_path: string;
  chunk_count: number;
  embedding_count: number;
  created_at: string;
  status: string;
  metadata?: Record<string, any>;
}

export interface UploadResponse {
  success: boolean;
  document_id: string;
  title: string;
  chunk_count: number;
  embeddings_created: number;
  message: string;
}

export interface RebuildIndexResponse {
  success: boolean;
  vectors_indexed: number;
  dimension: number;
  message: string;
}

export interface ContentCoverageResponse {
  chapter: string;
  document_count: number;
  chunk_count: number;
  topics_covered: string[];
  coverage_percentage: number;
}

export interface QualityCheckResponse {
  document_id: string;
  title: string;
  issues_found: string[];
  quality_score: number;
  recommendations: string[];
}

// Legacy interface (kept for backward compatibility)
export interface UploadedDocument {
  document_id: string;
  title: string;
  chapter: string;
  chunk_count: number;
  embeddings_created: number;
  created_at: string;
}

// ==================== ADMIN API ====================

export const adminApi = {
  /**
   * Get enhanced system statistics
   */
  async getStats(): Promise<SystemStats> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to get stats:', error);
      throw error;
    }
  },

  /**
   * Upload a PDF document with enhanced metadata
   */
  async uploadDocument(
    file: File,
    title: string,
    chapter: string,
    topic?: string,
    difficulty?: string,
    tags?: string
  ): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('chapter', chapter);
      if (topic) formData.append('topic', topic);
      if (difficulty) formData.append('difficulty', difficulty);
      if (tags) formData.append('tags', tags);

      const response = await fetch(`${API_BASE_URL}/admin/upload-document`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    }
  },

  /**
   * Get list of all documents
   */
  async getDocuments(
    chapter?: string,
    topic?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<DocumentInfo[]> {
    try {
      const params = new URLSearchParams();
      if (chapter) params.append('chapter', chapter);
      if (topic) params.append('topic', topic);
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());
      
      const response = await fetch(
        `${API_BASE_URL}/admin/documents?${params}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to get documents:', error);
      return [];
    }
  },

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<void> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/documents/${documentId}`,
        { method: 'DELETE' }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to delete document:', error);
      throw error;
    }
  },

  /**
   * Update document metadata
   */
  async updateDocument(
    documentId: string,
    updates: {
      title?: string;
      chapter?: string;
      topic?: string;
      difficulty?: string;
      tags?: string;
    }
  ): Promise<void> {
    try {
      const formData = new FormData();
      if (updates.title) formData.append('title', updates.title);
      if (updates.chapter) formData.append('chapter', updates.chapter);
      if (updates.topic) formData.append('topic', updates.topic);
      if (updates.difficulty) formData.append('difficulty', updates.difficulty);
      if (updates.tags) formData.append('tags', updates.tags);
      
      const response = await fetch(
        `${API_BASE_URL}/admin/documents/${documentId}`,
        {
          method: 'PUT',
          body: formData
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to update document:', error);
      throw error;
    }
  },

  /**
   * Get content coverage analysis
   */
  async getContentCoverage(): Promise<ContentCoverageResponse[]> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/content-coverage`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to get content coverage:', error);
      return [];
    }
  },

  /**
   * Run quality check on document
   */
  async qualityCheck(documentId: string): Promise<QualityCheckResponse> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/quality-check/${documentId}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to run quality check:', error);
      throw error;
    }
  },

  /**
   * Test a query (admin interface)
   */
  async testQuery(query: string): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('query', query);
      
      const response = await fetch(
        `${API_BASE_URL}/admin/test-query`,
        {
          method: 'POST',
          body: formData
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to test query:', error);
      throw error;
    }
  },

  /**
   * Rebuild FAISS index from database
   */
  async rebuildIndex(): Promise<RebuildIndexResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/rebuild-index`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to rebuild index:', error);
      throw error;
    }
  },

  /**
   * Initialize FAISS index
   */
  async initializeIndex(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/tutor/initialize-index`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to initialize index:', error);
      throw error;
    }
  },
};