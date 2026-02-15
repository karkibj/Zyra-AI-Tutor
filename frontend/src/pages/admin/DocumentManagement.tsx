import React, { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { adminApi,type DocumentInfo } from '../../services/adminApi';
import '../../styles/DocumentManagement.css';

const DocumentManagement: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [filteredDocs, setFilteredDocs] = useState<DocumentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState<DocumentInfo | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  
  // Filters
  const [chapterFilter, setChapterFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Upload form
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    title: '',
    chapter: 'algebra',
    topic: '',
    difficulty: 'medium',
    tags: ''
  });
  
  // Statistics
  const [stats, setStats] = useState({
    total: 0,
    byChapter: {} as Record<string, number>,
    byStatus: {} as Record<string, number>
  });

  useEffect(() => {
    loadDocuments();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [documents, chapterFilter, statusFilter, searchQuery]);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await adminApi.getDocuments();
      setDocuments(docs);
      calculateStats(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateStats = (docs: DocumentInfo[]) => {
    const byChapter: Record<string, number> = {};
    const byStatus: Record<string, number> = {};
    
    docs.forEach(doc => {
      byChapter[doc.chapter] = (byChapter[doc.chapter] || 0) + 1;
      byStatus[doc.status] = (byStatus[doc.status] || 0) + 1;
    });
    
    setStats({
      total: docs.length,
      byChapter,
      byStatus
    });
  };

  const applyFilters = () => {
    let filtered = [...documents];
    
    // Chapter filter
    if (chapterFilter !== 'all') {
      filtered = filtered.filter(doc => doc.chapter === chapterFilter);
    }
    
    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(doc => doc.status === statusFilter);
    }
    
    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(doc =>
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.chapter.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    setFilteredDocs(filtered);
  };

  const handleUploadSubmit = async () => {
    if (!uploadFile) {
      alert('Please select a file');
      return;
    }
    
    setIsUploading(true);
    try {
      await adminApi.uploadDocument(
        uploadFile,
        uploadForm.title || uploadFile.name.replace('.pdf', ''),
        uploadForm.chapter,
        uploadForm.topic,
        uploadForm.difficulty,
        uploadForm.tags
      );
      
      alert('✅ Document uploaded successfully!');
      setShowUploadModal(false);
      resetUploadForm();
      loadDocuments();
    } catch (error) {
      alert('❌ Upload failed. Please try again.');
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document? This cannot be undone.')) {
      return;
    }
    
    try {
      await adminApi.deleteDocument(docId);
      alert('✅ Document deleted successfully');
      loadDocuments();
    } catch (error) {
      alert('❌ Delete failed');
      console.error(error);
    }
  };

  const handleEdit = async () => {
    if (!selectedDoc) return;
    
    try {
      await adminApi.updateDocument(selectedDoc.document_id, uploadForm);
      alert('✅ Document updated successfully');
      setShowEditModal(false);
      loadDocuments();
    } catch (error) {
      alert('❌ Update failed');
      console.error(error);
    }
  };

  const resetUploadForm = () => {
    setUploadFile(null);
    setUploadForm({
      title: '',
      chapter: 'algebra',
      topic: '',
      difficulty: 'medium',
      tags: ''
    });
  };

  const openEditModal = (doc: DocumentInfo) => {
    setSelectedDoc(doc);
    setUploadForm({
      title: doc.title,
      chapter: doc.chapter,
      topic: doc.metadata?.topic || '',
      difficulty: doc.metadata?.difficulty || 'medium',
      tags: doc.metadata?.tags?.join(', ') || ''
    });
    setShowEditModal(true);
  };

  return (
    <AdminLayout>
      <div className="document-management">
        {/* Header */}
        <div className="dm-header">
          <div>
            <h1>📚 Document Management</h1>
            <p className="dm-subtitle">
              Manage curriculum documents and content organization
            </p>
          </div>
          <button 
            className="btn btn-primary"
            onClick={() => setShowUploadModal(true)}
          >
            ➕ Upload New Document
          </button>
        </div>

        {/* Statistics Cards */}
        <div className="dm-stats">
          <div className="stat-card">
            <div className="stat-icon">📄</div>
            <div className="stat-info">
              <div className="stat-value">{stats.total}</div>
              <div className="stat-label">Total Documents</div>
            </div>
          </div>
          
          {Object.entries(stats.byChapter).map(([chapter, count]) => (
            <div key={chapter} className="stat-card">
              <div className="stat-icon">📂</div>
              <div className="stat-info">
                <div className="stat-value">{count}</div>
                <div className="stat-label">{chapter}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="dm-filters">
          <div className="filter-group">
            <label>Search:</label>
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="filter-input"
            />
          </div>
          
          <div className="filter-group">
            <label>Chapter:</label>
            <select
              value={chapterFilter}
              onChange={(e) => setChapterFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Chapters</option>
              <option value="algebra">Algebra</option>
              <option value="geometry">Geometry</option>
              <option value="trigonometry">Trigonometry</option>
              <option value="statistics">Statistics</option>
              <option value="probability">Probability</option>
              <option value="general">General</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          
          <button 
            className="btn btn-secondary btn-sm"
            onClick={loadDocuments}
          >
            🔄 Refresh
          </button>
        </div>

        {/* Documents Table */}
        <div className="dm-table-container">
          {isLoading ? (
            <div className="dm-loading">
              <div className="loading-spinner"></div>
              <p>Loading documents...</p>
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="dm-empty">
              <p>📭 No documents found</p>
              <p className="dm-empty-hint">
                {searchQuery || chapterFilter !== 'all' || statusFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Upload your first document to get started'}
              </p>
            </div>
          ) : (
            <table className="dm-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Chapter</th>
                  <th>Chunks</th>
                  <th>Embeddings</th>
                  <th>Status</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.map(doc => (
                  <tr key={doc.document_id}>
                    <td className="dm-title">{doc.title}</td>
                    <td>
                      <span className="badge badge-chapter">{doc.chapter}</span>
                    </td>
                    <td className="dm-count">{doc.chunk_count}</td>
                    <td className="dm-count">{doc.embedding_count}</td>
                    <td>
                      <span className={`badge badge-${doc.status}`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="dm-date">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="dm-actions">
                      <button
                        className="action-btn action-edit"
                        onClick={() => openEditModal(doc)}
                        title="Edit"
                      >
                        ✏️
                      </button>
                      <button
                        className="action-btn action-delete"
                        onClick={() => handleDelete(doc.document_id)}
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>📤 Upload New Document</h2>
                <button className="modal-close" onClick={() => setShowUploadModal(false)}>
                  ✖
                </button>
              </div>
              
              <div className="modal-body">
                <div className="form-group">
                  <label>PDF File *</label>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Title *</label>
                  <input
                    type="text"
                    placeholder="e.g., Quadratic Equations Chapter"
                    value={uploadForm.title}
                    onChange={(e) => setUploadForm({...uploadForm, title: e.target.value})}
                    className="form-input"
                  />
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>Chapter *</label>
                    <select
                      value={uploadForm.chapter}
                      onChange={(e) => setUploadForm({...uploadForm, chapter: e.target.value})}
                      className="form-select"
                    >
                      <option value="algebra">Algebra</option>
                      <option value="geometry">Geometry</option>
                      <option value="trigonometry">Trigonometry</option>
                      <option value="statistics">Statistics</option>
                      <option value="probability">Probability</option>
                      <option value="mensuration">Mensuration</option>
                      <option value="general">General</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Difficulty</label>
                    <select
                      value={uploadForm.difficulty}
                      onChange={(e) => setUploadForm({...uploadForm, difficulty: e.target.value})}
                      className="form-select"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                </div>
                
                <div className="form-group">
                  <label>Topic (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g., Quadratic Formula, Discriminant"
                    value={uploadForm.topic}
                    onChange={(e) => setUploadForm({...uploadForm, topic: e.target.value})}
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Tags (Optional)</label>
                  <input
                    type="text"
                    placeholder="comma, separated, tags"
                    value={uploadForm.tags}
                    onChange={(e) => setUploadForm({...uploadForm, tags: e.target.value})}
                    className="form-input"
                  />
                  <small className="form-hint">Separate tags with commas</small>
                </div>
              </div>
              
              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowUploadModal(false);
                    resetUploadForm();
                  }}
                  disabled={isUploading}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleUploadSubmit}
                  disabled={!uploadFile || isUploading}
                >
                  {isUploading ? 'Uploading...' : 'Upload & Process'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {showEditModal && selectedDoc && (
          <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>✏️ Edit Document</h2>
                <button className="modal-close" onClick={() => setShowEditModal(false)}>
                  ✖
                </button>
              </div>
              
              <div className="modal-body">
                <div className="form-group">
                  <label>Title *</label>
                  <input
                    type="text"
                    value={uploadForm.title}
                    onChange={(e) => setUploadForm({...uploadForm, title: e.target.value})}
                    className="form-input"
                  />
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>Chapter *</label>
                    <select
                      value={uploadForm.chapter}
                      onChange={(e) => setUploadForm({...uploadForm, chapter: e.target.value})}
                      className="form-select"
                    >
                      <option value="algebra">Algebra</option>
                      <option value="geometry">Geometry</option>
                      <option value="trigonometry">Trigonometry</option>
                      <option value="statistics">Statistics</option>
                      <option value="probability">Probability</option>
                      <option value="general">General</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Difficulty</label>
                    <select
                      value={uploadForm.difficulty}
                      onChange={(e) => setUploadForm({...uploadForm, difficulty: e.target.value})}
                      className="form-select"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                </div>
                
                <div className="form-group">
                  <label>Topic</label>
                  <input
                    type="text"
                    value={uploadForm.topic}
                    onChange={(e) => setUploadForm({...uploadForm, topic: e.target.value})}
                    className="form-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Tags</label>
                  <input
                    type="text"
                    value={uploadForm.tags}
                    onChange={(e) => setUploadForm({...uploadForm, tags: e.target.value})}
                    className="form-input"
                  />
                </div>
              </div>
              
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowEditModal(false)}>
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={handleEdit}>
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
};

export default DocumentManagement;