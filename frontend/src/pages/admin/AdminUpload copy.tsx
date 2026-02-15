import React, { useState, useRef, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { adminApi, type DocumentInfo } from '../../services/adminApi';
import '../../styles/AdminUpload.css';

const AdminUpload: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [formData, setFormData] = useState({
    title: '',
    chapter: '',
  });

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const docs = await adminApi.getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      alert('Please upload a PDF file');
      return;
    }

    if (!formData.title) {
      // Auto-fill title from filename
      const titleFromFile = file.name.replace('.pdf', '').replace(/_/g, ' ');
      setFormData(prev => ({ ...prev, title: titleFromFile }));
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const result = await adminApi.uploadDocument(
        file,
        formData.title || file.name.replace('.pdf', ''),
        formData.chapter || 'general'
      );

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Success!
      setTimeout(() => {
        alert(`✅ Document uploaded successfully!\n\nDocument ID: ${result.document_id}\nChunks created: ${result.chunk_count}\nEmbeddings: ${result.embeddings_created}`);
        
        // Reset form
        setFormData({ title: '', chapter: '' });
        setUploadProgress(0);
        loadDocuments(); // Reload document list
      }, 500);

    } catch (error) {
      alert('❌ Upload failed. Please try again.');
      console.error('Upload error:', error);
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleClickUpload = () => {
    fileInputRef.current?.click();
  };

  return (
    <AdminLayout>
      <div className="admin-upload">
        <header className="upload-header">
          <h1>📤 Content Management</h1>
          <p className="upload-subtitle">
            Upload curriculum documents to expand Zyra's knowledge base
          </p>
        </header>

        {/* Upload Form */}
        <div className="upload-section">
          <h2>Upload New Document</h2>
          
          <div className="upload-form">
            <div className="form-group">
              <label htmlFor="title">Document Title</label>
              <input
                type="text"
                id="title"
                placeholder="e.g., Quadratic Equations Chapter"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="chapter">Chapter / Topic</label>
              <select
                id="chapter"
                value={formData.chapter}
                onChange={(e) => setFormData(prev => ({ ...prev, chapter: e.target.value }))}
                className="form-select"
              >
                <option value="">Select chapter...</option>
                <option value="algebra">Algebra</option>
                <option value="geometry">Geometry</option>
                <option value="trigonometry">Trigonometry</option>
                <option value="statistics">Statistics</option>
                <option value="probability">Probability</option>
                <option value="sets">Sets</option>
                <option value="mensuration">Mensuration</option>
                <option value="general">General / Mixed Topics</option>
              </select>
            </div>
          </div>

          {/* Drag & Drop Area */}
          <div
            className={`drop-zone ${isDragging ? 'drop-zone-active' : ''} ${isUploading ? 'drop-zone-uploading' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={!isUploading ? handleClickUpload : undefined}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
              disabled={isUploading}
            />

            {isUploading ? (
              <div className="upload-progress">
                <div className="progress-spinner"></div>
                <p className="progress-text">Uploading... {uploadProgress}%</p>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="progress-detail">Processing PDF, generating chunks & embeddings...</p>
              </div>
            ) : (
              <>
                <div className="drop-icon">📄</div>
                <h3>Drag & Drop PDF Here</h3>
                <p>or click to browse files</p>
                <p className="drop-hint">Only PDF files are supported</p>
              </>
            )}
          </div>
        </div>

        {/* Documents List */}
        <div className="documents-section">
          <div className="documents-header">
            <h2>📚 Uploaded Documents ({documents.length})</h2>
            <button 
              className="btn btn-secondary btn-sm"
              onClick={loadDocuments}
              disabled={isLoadingDocs}
            >
              🔄 Refresh
            </button>
          </div>

          {isLoadingDocs ? (
            <div className="documents-loading">
              <div className="loading-spinner"></div>
              <p>Loading documents...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="documents-empty">
              <p>📭 No documents uploaded yet</p>
              <p className="empty-hint">Upload your first document to get started!</p>
            </div>
          ) : (
            <div className="documents-grid">
              {documents.map((doc) => (
                <div key={doc.document_id} className="document-card">
                  <div className="document-icon">📄</div>
                  <div className="document-info">
                    <h3 className="document-title">{doc.title}</h3>
                    <div className="document-meta">
                      <span className="meta-item">
                        📂 {doc.chapter}
                      </span>
                      <span className="meta-item">
                        📊 {doc.chunk_count} chunks
                      </span>
                      <span className="meta-item">
                        🧠 {doc.embedding_count} embeddings
                      </span>
                    </div>
                    <div className="document-date">
                      Uploaded: {new Date(doc.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="upload-stats">
          <div className="stat-box">
            <div className="stat-number">{documents.length}</div>
            <div className="stat-label">Total Documents</div>
          </div>
          <div className="stat-box">
            <div className="stat-number">
              {documents.reduce((sum, doc) => sum + doc.chunk_count, 0)}
            </div>
            <div className="stat-label">Total Chunks</div>
          </div>
          <div className="stat-box">
            <div className="stat-number">
              {documents.reduce((sum, doc) => sum + doc.embedding_count, 0)}
            </div>
            <div className="stat-label">Total Embeddings</div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminUpload;