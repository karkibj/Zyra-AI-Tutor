import React, { useState, useEffect } from 'react';
import { Upload, FileText, Download, Eye, Trash2, CheckCircle, Clock, AlertCircle, Calendar, MapPin, X, RefreshCw } from 'lucide-react';
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

const API = 'http://localhost:8000/api/v1';

const PROVINCES = ['Koshi', 'Madhesh', 'Bagmati', 'Gandaki', 'Lumbini', 'Karnali', 'Sudurpashchim'];
const CURRENT_YEAR = 2082;
const YEARS = Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - i);

// ── Toast ────────────────────────────────────────────────────────────────────
const Toast: React.FC<{ message: string; type: 'success' | 'error'; onClose: () => void }> = ({ message, type, onClose }) => (
  <div style={{
    position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999,
    display: 'flex', alignItems: 'center', gap: '10px',
    background: type === 'success' ? '#d1fae5' : '#fee2e2',
    border: `1px solid ${type === 'success' ? '#6ee7b7' : '#fca5a5'}`,
    color: type === 'success' ? '#065f46' : '#991b1b',
    padding: '12px 16px', borderRadius: '10px',
    fontSize: '14px', fontWeight: 500,
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    animation: 'slideIn 0.2s ease-out'
  }}>
    {type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
    {message}
    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', marginLeft: '4px' }}>
      <X size={14} />
    </button>
  </div>
);

// ── Delete Modal ─────────────────────────────────────────────────────────────
const DeleteModal: React.FC<{
  title: string;
  onConfirm: () => void;
  onCancel: () => void;
  deleting: boolean;
}> = ({ title, onConfirm, onCancel, deleting }) => (
  <div style={{
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9998
  }}>
    <div style={{
      background: '#fff', borderRadius: '12px', padding: '24px',
      maxWidth: '400px', width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        <div style={{ width: '40px', height: '40px', background: '#fee2e2', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Trash2 size={20} color="#ef4444" />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '16px', color: '#111827' }}>Delete past paper</div>
          <div style={{ fontSize: '13px', color: '#6b7280' }}>This cannot be undone</div>
        </div>
      </div>
      <p style={{ fontSize: '14px', color: '#374151', marginBottom: '20px', background: '#f9fafb', padding: '10px', borderRadius: '8px' }}>
        "{title}"
      </p>
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
        <button onClick={onCancel} disabled={deleting} style={{
          padding: '8px 16px', border: '1px solid #d1d5db', borderRadius: '8px',
          background: '#fff', color: '#374151', cursor: 'pointer', fontSize: '14px'
        }}>Cancel</button>
        <button onClick={onConfirm} disabled={deleting} style={{
          padding: '8px 16px', background: deleting ? '#fca5a5' : '#ef4444',
          border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer', fontSize: '14px', fontWeight: 500
        }}>{deleting ? 'Deleting...' : 'Delete'}</button>
      </div>
    </div>
  </div>
);

export const PastPapersTab: React.FC = () => {
  const [papers, setPapers]             = useState<PastPaper[]>([]);
  const [loading, setLoading]           = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<PastPaper | null>(null);
  const [deleting, setDeleting]         = useState(false);
  const [toast, setToast]               = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Upload form
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadYear, setUploadYear]     = useState<number>(CURRENT_YEAR);
  const [uploadProvince, setUploadProvince] = useState('');
  const [uploadTitle, setUploadTitle]   = useState('');
  const [uploading, setUploading]       = useState(false);

  useEffect(() => { loadPapers(); }, []);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const loadPapers = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/past-papers/admin-list`);
      setPapers(res.data.papers || []);
    } catch {
      showToast('Failed to load papers', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleView = (paper: PastPaper) => {
    window.open(`${API}/admin/content/view/${paper.id}`, '_blank');
  };

  const handleDownload = (paper: PastPaper) => {
    window.open(`${API}/admin/content/download/${paper.id}`, '_blank');
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await axios.delete(`${API}/admin/content/${deleteTarget.id}`);
      setPapers(prev => prev.filter(p => p.id !== deleteTarget.id));
      showToast(`"${deleteTarget.title}" deleted successfully`, 'success');
    } catch {
      showToast('Delete failed. Please try again.', 'error');
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (uploadProvince) setUploadTitle(`SEE ${uploadYear} Mathematics - ${uploadProvince} Province`);
    }
  };

  const handleProvinceChange = (province: string) => {
    setUploadProvince(province);
    setUploadTitle(`SEE ${uploadYear} Mathematics - ${province} Province`);
  };

  const handleYearChange = (year: number) => {
    setUploadYear(year);
    if (uploadProvince) setUploadTitle(`SEE ${year} Mathematics - ${uploadProvince} Province`);
  };

  const handleUpload = async () => {
    if (!selectedFile || !uploadProvince) {
      showToast('Please select a file and province', 'error');
      return;
    }
    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('year', uploadYear.toString());
    formData.append('province', uploadProvince);
    formData.append('title', uploadTitle);
    try {
      await axios.post(`${API}/admin/upload/past-paper`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      showToast('Past paper uploaded! Processing will begin shortly.', 'success');
      setShowUploadModal(false);
      setSelectedFile(null);
      setUploadProvince('');
      setUploadTitle('');
      loadPapers();
    } catch {
      showToast('Upload failed. Please try again.', 'error');
    } finally {
      setUploading(false);
    }
  };

  const resetUploadForm = () => {
    setShowUploadModal(false);
    setSelectedFile(null);
    setUploadProvince('');
    setUploadTitle('');
  };

  const getStatusBadge = (status: string) => {
    const cfg: Record<string, { icon: any; bg: string; color: string; label: string }> = {
      completed:  { icon: CheckCircle, bg: '#d1fae5', color: '#065f46', label: 'Ready' },
      processing: { icon: Clock,        bg: '#fef3c7', color: '#92400e', label: 'Processing' },
      pending:    { icon: Clock,        bg: '#f3f4f6', color: '#374151', label: 'Pending' },
      failed:     { icon: AlertCircle,  bg: '#fee2e2', color: '#991b1b', label: 'Failed' },
    };
    const c = cfg[status] || cfg.pending;
    const Icon = c.icon;
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: c.bg, color: c.color, padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: 600 }}>
        <Icon size={12} />{c.label}
      </span>
    );
  };

  const formatSize = (bytes: number) => bytes ? (bytes / 1024 / 1024).toFixed(1) + ' MB' : '—';
  const papersByYear = papers.reduce((acc, p) => {
    const y = p.year || 'Unknown';
    if (!acc[y]) acc[y] = [];
    acc[y].push(p);
    return acc;
  }, {} as Record<number | string, PastPaper[]>);

  return (
    <div className="past-papers-tab">
      {/* Header */}
      <div className="tab-header">
        <div>
          <h2>Past Papers Management</h2>
          <p>Upload and manage SEE Mathematics past papers</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={loadPapers} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => setShowUploadModal(true)} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Upload size={16} /> Upload Past Paper
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-row">
        {[
          { label: 'Total Papers', value: papers.length },
          { label: 'Ready', value: papers.filter(p => p.processing_status === 'completed').length },
          { label: 'Processing', value: papers.filter(p => p.processing_status === 'processing').length },
          { label: 'Years', value: Object.keys(papersByYear).length },
        ].map(({ label, value }) => (
          <div className="stat-box" key={label}>
            <span className="stat-value">{value}</span>
            <span className="stat-label">{label}</span>
          </div>
        ))}
      </div>

      {/* Papers grouped by year */}
      <div className="papers-list">
        {loading ? (
          <div className="loading" style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
            <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 8px', display: 'block' }} />
            Loading papers...
          </div>
        ) : papers.length === 0 ? (
          <div className="empty-state" style={{ textAlign: 'center', padding: '3rem', color: '#6b7280' }}>
            <FileText size={64} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
            <h3 style={{ margin: '0 0 8px', color: '#374151' }}>No past papers yet</h3>
            <p style={{ margin: 0 }}>Click "Upload Past Paper" to add your first paper</p>
          </div>
        ) : (
          Object.keys(papersByYear).sort((a, b) => Number(b) - Number(a)).map(year => (
            <div key={year} className="year-group">
              <h3 className="year-header" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px', fontWeight: 600, margin: '0 0 12px', color: '#374151' }}>
                <Calendar size={18} /> SEE {year}
                <span style={{ fontSize: '13px', fontWeight: 400, color: '#9ca3af' }}>
                  ({papersByYear[year].length} paper{papersByYear[year].length !== 1 ? 's' : ''})
                </span>
              </h3>
              <div className="papers-grid">
                {papersByYear[year].map(paper => (
                  <div key={paper.id} className="paper-card">
                    <div className="paper-header">
                      <div style={{ width: '40px', height: '40px', background: '#e0e7ff', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <FileText size={20} color="#4338ca" />
                      </div>
                      <div className="paper-info">
                        <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#111827' }}>
                          {paper.province} Province
                        </h4>
                        <p className="paper-meta" style={{ display: 'flex', alignItems: 'center', gap: '4px', margin: '2px 0 0', fontSize: '12px', color: '#6b7280' }}>
                          <MapPin size={12} /> {paper.province} · {paper.page_count || '?'} pages
                        </p>
                      </div>
                    </div>

                    <div className="paper-stats" style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#6b7280', margin: '8px 0' }}>
                      <span>{formatSize(paper.file_size)}</span>
                      <span>{paper.chunks_count || 0} chunks</span>
                    </div>

                    <div style={{ margin: '8px 0' }}>
                      {getStatusBadge(paper.processing_status)}
                    </div>

                    <div className="paper-actions" style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                      <button
                        className="btn-icon" title="View PDF"
                        onClick={() => handleView(paper)}
                        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '32px', height: '32px', border: '1px solid #e5e7eb', borderRadius: '6px', background: '#fff' }}
                      >
                        <Eye size={15} />
                      </button>
                      <button
                        className="btn-icon" title="Download"
                        onClick={() => handleDownload(paper)}
                        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '32px', height: '32px', border: '1px solid #e5e7eb', borderRadius: '6px', background: '#fff' }}
                      >
                        <Download size={15} />
                      </button>
                      <button
                        className="btn-icon danger" title="Delete"
                        onClick={() => setDeleteTarget(paper)}
                        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '32px', height: '32px', border: '1px solid #fca5a5', borderRadius: '6px', background: '#fee2e2', color: '#ef4444' }}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9998 }}>
          <div style={{ background: '#fff', borderRadius: '16px', padding: '28px', maxWidth: '480px', width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#111827' }}>Upload Past Paper</h2>
              <button onClick={resetUploadForm} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>Year *</label>
                <select value={uploadYear} onChange={e => handleYearChange(Number(e.target.value))}
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '14px' }}>
                  {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>Province *</label>
                <select value={uploadProvince} onChange={e => handleProvinceChange(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '14px' }}>
                  <option value="">Select Province</option>
                  {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>Title (auto-generated)</label>
                <input type="text" value={uploadTitle} onChange={e => setUploadTitle(e.target.value)}
                  placeholder="Auto-generated from year and province"
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box' }} />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>PDF File *</label>
                <label style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                  padding: '24px', border: '2px dashed #d1d5db', borderRadius: '10px',
                  cursor: 'pointer', background: selectedFile ? '#f0fdf4' : '#f9fafb',
                  borderColor: selectedFile ? '#6ee7b7' : '#d1d5db', textAlign: 'center'
                }}>
                  <input type="file" accept=".pdf" onChange={handleFileSelect} style={{ display: 'none' }} />
                  <Upload size={28} color={selectedFile ? '#10b981' : '#9ca3af'} />
                  <p style={{ margin: '8px 0 0', fontSize: '14px', color: selectedFile ? '#065f46' : '#6b7280', fontWeight: selectedFile ? 600 : 400 }}>
                    {selectedFile ? selectedFile.name : 'Click to select PDF'}
                  </p>
                  {selectedFile && <span style={{ fontSize: '12px', color: '#9ca3af' }}>{(selectedFile.size / 1024 / 1024).toFixed(1)} MB</span>}
                </label>
              </div>

              <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '12px', fontSize: '13px', color: '#1e40af' }}>
                ✅ Auto-maps to all 14 CDC chapters &nbsp;·&nbsp; ✅ Auto-processing enabled
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '24px' }}>
              <button onClick={resetUploadForm} disabled={uploading}
                style={{ padding: '10px 20px', border: '1px solid #d1d5db', borderRadius: '8px', background: '#fff', color: '#374151', cursor: 'pointer', fontSize: '14px' }}>
                Cancel
              </button>
              <button onClick={handleUpload} disabled={uploading || !selectedFile || !uploadProvince}
                style={{ padding: '10px 20px', background: uploading || !selectedFile || !uploadProvince ? '#a5b4fc' : '#6366f1', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer', fontSize: '14px', fontWeight: 500 }}>
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {deleteTarget && (
        <DeleteModal
          title={deleteTarget.title}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeleteTarget(null)}
          deleting={deleting}
        />
      )}

      {/* Toast */}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default PastPapersTab;