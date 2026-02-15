import React, { useState, useEffect } from 'react';
import { Upload, FileText, Download, Eye, Trash2, CheckCircle, Clock, AlertCircle, Calendar, MapPin } from 'lucide-react';
import axios from 'axios';


interface PastPaper {
  id: string;
  title: string;
  year: number;
  province: string;
  processing_status: string;
  chunks_count: number;
  page_count: number;
  file_size: number;
  created_at: string;
}

const PROVINCES = [
  'Koshi',
  'Madhesh',
  'Bagmati',
  'Gandaki',
  'Lumbini',
  'Karnali',
  'Sudurpashchim'
];

const CURRENT_YEAR = 2082;
const YEARS = Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - i); // 2080, 2079, 2078, 2077, 2076

export const PastPapersTab: React.FC = () => {
  const [papers, setPapers] = useState<PastPaper[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  
  // Upload form state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadYear, setUploadYear] = useState<number>(CURRENT_YEAR);
  const [uploadProvince, setUploadProvince] = useState<string>('');
  const [uploadTitle, setUploadTitle] = useState<string>('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadPapers();
  }, []);

  const loadPapers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/v1/admin/past-papers/admin-list');
      setPapers(response.data.papers || []);
    } catch (error) {
      console.error('Error loading past papers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Auto-generate title if not set
      if (!uploadTitle && uploadProvince) {
        setUploadTitle(`SEE ${uploadYear} Mathematics - ${uploadProvince} Province`);
      }
    }
  };

  const handleProvinceChange = (province: string) => {
    setUploadProvince(province);
    setUploadTitle(`SEE ${uploadYear} Mathematics - ${province} Province`);
  };

  const handleYearChange = (year: number) => {
    setUploadYear(year);
    if (uploadProvince) {
      setUploadTitle(`SEE ${year} Mathematics - ${uploadProvince} Province`);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !uploadProvince) {
      alert('Please select a file and province');
      return;
    }

    setUploading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('year', uploadYear.toString());
    formData.append('province', uploadProvince);
    formData.append('title', uploadTitle);

    try {
      await axios.post('http://localhost:8000/api/v1/admin/upload/past-paper', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      alert('✅ Past paper uploaded! Auto-processing will begin shortly.');
      
      // Reset form
      setShowUploadModal(false);
      setSelectedFile(null);
      setUploadProvince('');
      setUploadTitle('');
      
      // Reload list
      loadPapers();
    } catch (error) {
      console.error('Upload error:', error);
      alert('❌ Upload failed. Check console.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string, title: string) => {
    if (!window.confirm(`Delete "${title}"?`)) return;

    try {
      await axios.delete(`http://localhost:8000/api/v1/admin/content/${id}`);
      alert('✅ Deleted successfully');
      loadPapers();
    } catch (error) {
      console.error('Delete error:', error);
      alert('❌ Delete failed');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { icon: any; className: string; label: string }> = {
      completed: { icon: CheckCircle, className: 'status-completed', label: 'Ready' },
      processing: { icon: Clock, className: 'status-processing', label: 'Processing' },
      pending: { icon: Clock, className: 'status-pending', label: 'Pending' },
      failed: { icon: AlertCircle, className: 'status-failed', label: 'Failed' }
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <span className={`status-badge ${config.className}`}>
        <Icon size={14} />
        {config.label}
      </span>
    );
  };

  const formatFileSize = (bytes: number) => {
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  // Group papers by year
  const papersByYear = papers.reduce((acc, paper) => {
    const year = paper.year || 'Unknown';
    if (!acc[year]) acc[year] = [];
    acc[year].push(paper);
    return acc;
  }, {} as Record<number | string, PastPaper[]>);

  return (
    <div className="past-papers-tab">
      {/* Header */}
      <div className="tab-header">
        <div>
          <h2>📄 Past Papers Management</h2>
          <p>Upload and manage SEE Mathematics past papers</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUploadModal(true)}>
          <Upload size={20} />
          Upload Past Paper
        </button>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-box">
          <span className="stat-value">{papers.length}</span>
          <span className="stat-label">Total Papers</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">{papers.filter(p => p.processing_status === 'completed').length}</span>
          <span className="stat-label">Ready</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">{papers.filter(p => p.processing_status === 'processing').length}</span>
          <span className="stat-label">Processing</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">{Object.keys(papersByYear).length}</span>
          <span className="stat-label">Years</span>
        </div>
      </div>

      {/* Papers List - Grouped by Year */}
      <div className="papers-list">
        {loading ? (
          <div className="loading">Loading papers...</div>
        ) : (
          <>
            {Object.keys(papersByYear)
              .sort((a, b) => Number(b) - Number(a))
              .map(year => (
                <div key={year} className="year-group">
                  <h3 className="year-header">
                    <Calendar size={20} />
                    SEE {year}
                  </h3>

                  <div className="papers-grid">
                    {papersByYear[year].map(paper => (
                      <div key={paper.id} className="paper-card">
                        <div className="paper-header">
                          <FileText size={24} />
                          <div className="paper-info">
                            <h4>{paper.province} Province</h4>
                            <p className="paper-meta">
                              <MapPin size={14} />
                              {paper.province} • {paper.page_count || '?'} pages
                            </p>
                          </div>
                        </div>

                        <div className="paper-stats">
                          <span>{formatFileSize(paper.file_size)}</span>
                          <span>{paper.chunks_count || 0} chunks</span>
                        </div>

                        <div className="paper-status">
                          {getStatusBadge(paper.processing_status)}
                        </div>

                        <div className="paper-actions">
                          <button className="btn-icon" title="View">
                            <Eye size={16} />
                          </button>
                          <button className="btn-icon" title="Download">
                            <Download size={16} />
                          </button>
                          <button 
                            className="btn-icon danger" 
                            title="Delete"
                            onClick={() => handleDelete(paper.id, paper.title)}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

            {papers.length === 0 && (
              <div className="empty-state">
                <FileText size={64} />
                <h3>No past papers uploaded yet</h3>
                <p>Click "Upload Past Paper" to add your first paper</p>
              </div>
            )}
          </>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📤 Upload Past Paper</h2>
              <button className="btn-close" onClick={() => setShowUploadModal(false)}>×</button>
            </div>

            <div className="modal-body">
              {/* Year Selection */}
              <div className="form-group">
                <label>Year *</label>
                <select 
                  value={uploadYear} 
                  onChange={e => handleYearChange(Number(e.target.value))}
                >
                  {YEARS.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>

              {/* Province Selection */}
              <div className="form-group">
                <label>Province *</label>
                <select 
                  value={uploadProvince} 
                  onChange={e => handleProvinceChange(e.target.value)}
                >
                  <option value="">Select Province</option>
                  {PROVINCES.map(province => (
                    <option key={province} value={province}>{province}</option>
                  ))}
                </select>
              </div>

              {/* Title (Auto-generated) */}
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={uploadTitle}
                  onChange={e => setUploadTitle(e.target.value)}
                  placeholder="Auto-generated from year and province"
                />
              </div>

              {/* File Upload */}
              <div className="form-group">
                <label>PDF File *</label>
                <div className="file-upload-area">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    id="pdf-file"
                  />
                  <label htmlFor="pdf-file" className="file-upload-label">
                    <Upload size={32} />
                    <p>{selectedFile ? selectedFile.name : 'Click to select PDF'}</p>
                    {selectedFile && (
                      <span className="file-size">{formatFileSize(selectedFile.size)}</span>
                    )}
                  </label>
                </div>
              </div>

              {/* Info Box */}
              <div className="info-box">
                <p>✅ Auto-maps to all 14 chapters</p>
                <p>✅ Auto-processing enabled</p>
                <p>✅ Will be available for students once processed</p>
              </div>
            </div>

            <div className="modal-footer">
              <button 
                className="btn-secondary" 
                onClick={() => setShowUploadModal(false)}
                disabled={uploading}
              >
                Cancel
              </button>
              <button 
                className="btn-primary" 
                onClick={handleUpload}
                disabled={uploading || !selectedFile || !uploadProvince}
              >
                {uploading ? 'Uploading...' : 'Upload Past Paper'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PastPapersTab;