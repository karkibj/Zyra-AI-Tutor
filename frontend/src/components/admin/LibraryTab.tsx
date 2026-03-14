import React, { useState, useEffect } from 'react';
import { Search, Filter, Eye, Download, Trash2, FileText, CheckCircle, Clock, AlertCircle, RefreshCw, X } from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  content_type: string;
  file_path: string;
  processing_status: string;
  chunks_count: number;
  page_count: number;
  file_size: number;
  created_at: string;
}

const API = 'http://localhost:8000/api/v1';

// Simple toast notification
const Toast: React.FC<{ message: string; type: 'success' | 'error'; onClose: () => void }> = ({ message, type, onClose }) => (
  <div style={{
    position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999,
    display: 'flex', alignItems: 'center', gap: '10px',
    background: type === 'success' ? '#d1fae5' : '#fee2e2',
    border: `1px solid ${type === 'success' ? '#6ee7b7' : '#fca5a5'}`,
    color: type === 'success' ? '#065f46' : '#991b1b',
    padding: '12px 16px', borderRadius: '10px',
    fontSize: '14px', fontWeight: 500,
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
  }}>
    {type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
    {message}
    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', marginLeft: '4px', color: 'inherit' }}>
      <X size={14} />
    </button>
  </div>
);

// Delete confirm modal
const DeleteModal: React.FC<{
  item: ContentItem;
  onConfirm: () => void;
  onCancel: () => void;
  deleting: boolean;
}> = ({ item, onConfirm, onCancel, deleting }) => (
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
          <div style={{ fontWeight: 600, fontSize: '16px', color: '#111827' }}>Delete content</div>
          <div style={{ fontSize: '13px', color: '#6b7280' }}>This cannot be undone</div>
        </div>
      </div>
      <p style={{ fontSize: '14px', color: '#374151', marginBottom: '20px', background: '#f9fafb', padding: '10px', borderRadius: '8px' }}>
        "{item.title}"
      </p>
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
        <button onClick={onCancel} disabled={deleting} style={{
          padding: '8px 16px', border: '1px solid #d1d5db', borderRadius: '8px',
          background: '#fff', color: '#374151', cursor: 'pointer', fontSize: '14px'
        }}>
          Cancel
        </button>
        <button onClick={onConfirm} disabled={deleting} style={{
          padding: '8px 16px', background: deleting ? '#fca5a5' : '#ef4444',
          border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer', fontSize: '14px', fontWeight: 500
        }}>
          {deleting ? 'Deleting...' : 'Delete'}
        </button>
      </div>
    </div>
  </div>
);

export const LibraryTab: React.FC = () => {
  const [content, setContent]       = useState<ContentItem[]>([]);
  const [loading, setLoading]       = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [deleteTarget, setDeleteTarget] = useState<ContentItem | null>(null);
  const [deleting, setDeleting]     = useState(false);
  const [toast, setToast]           = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => { fetchContent(); }, [filterType]);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchContent = async () => {
    setLoading(true);
    try {
      let url = `${API}/admin/content/list?limit=100`;
      if (filterType !== 'all') url += `&content_type=${filterType}`;
      const res = await fetch(url);
      const data = await res.json();
      setContent(data.items || []);
    } catch {
      showToast('Failed to load content', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleView = (item: ContentItem) => {
    window.open(`${API}/admin/content/view/${item.id}`, '_blank');
  };

  const handleDownload = (item: ContentItem) => {
    window.open(`${API}/admin/content/download/${item.id}`, '_blank');
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API}/admin/content/${deleteTarget.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      setContent(prev => prev.filter(c => c.id !== deleteTarget.id));
      showToast(`"${deleteTarget.title}" deleted successfully`, 'success');
    } catch {
      showToast('Delete failed. Please try again.', 'error');
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  const filteredContent = content.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || item.processing_status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle size={14} color="#10b981" />;
    if (status === 'processing') return <Clock size={14} color="#f59e0b" />;
    if (status === 'failed') return <AlertCircle size={14} color="#ef4444" />;
    return <Clock size={14} color="#9ca3af" />;
  };

  const getTypeBadgeColor = (type: string): { bg: string; color: string } => {
    const map: Record<string, { bg: string; color: string }> = {
      curriculum:     { bg: '#ede9fe', color: '#7c3aed' },
      past_paper:     { bg: '#e0e7ff', color: '#4338ca' },
      model_question: { bg: '#dbeafe', color: '#1d4ed8' },
      solution:       { bg: '#d1fae5', color: '#065f46' },
      explanation:    { bg: '#fef3c7', color: '#92400e' },
      teacher_note:   { bg: '#fce7f3', color: '#9d174d' },
    };
    return map[type] || { bg: '#f3f4f6', color: '#374151' };
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return '—';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  };

  return (
    <div className="library-container">
      {/* Header */}
      <div className="library-header">
        <div>
          <h2>Content Library</h2>
          <p>Browse and manage all uploaded content</p>
        </div>
        <button className="btn btn-primary" onClick={fetchContent} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Stats Bar */}
      <div className="library-stats">
        {[
          { label: 'Total', value: content.length, color: '#6366f1' },
          { label: 'Completed', value: content.filter(c => c.processing_status === 'completed').length, color: '#10b981' },
          { label: 'Processing', value: content.filter(c => c.processing_status === 'processing').length, color: '#f59e0b' },
          { label: 'Failed', value: content.filter(c => c.processing_status === 'failed').length, color: '#ef4444' },
        ].map(({ label, value, color }) => (
          <div className="stat-item" key={label}>
            <span className="stat-label">{label}</span>
            <span className="stat-value" style={{ color }}>{value}</span>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="library-filters">
        <div className="search-box">
          <Search className="search-icon" size={16} />
          <input
            type="text"
            placeholder="Search content..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>
        <div className="filter-group">
          <Filter size={16} />
          <select value={filterType} onChange={e => setFilterType(e.target.value)} className="filter-select">
            <option value="all">All Types</option>
            <option value="curriculum">Curriculum</option>
            <option value="past_paper">Past Papers</option>
            <option value="model_question">Model Questions</option>
            <option value="solution">Solutions</option>
            <option value="explanation">Explanations</option>
            <option value="teacher_note">Teacher Notes</option>
          </select>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="filter-select">
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Content Grid */}
      {loading ? (
        <div className="loading-container"><div className="loading-spinner" /></div>
      ) : filteredContent.length === 0 ? (
        <div className="empty-state">
          <FileText size={64} className="empty-icon" />
          <h3>No content found</h3>
          <p>Try adjusting your filters or upload new content</p>
        </div>
      ) : (
        <div className="content-grid">
          {filteredContent.map(item => {
            const badge = getTypeBadgeColor(item.content_type);
            return (
              <div key={item.id} className="content-card">
                <div className="content-card-header">
                  <FileText className="content-icon" size={20} />
                  <span style={{
                    background: badge.bg, color: badge.color,
                    fontSize: '11px', fontWeight: 600, padding: '2px 8px',
                    borderRadius: '99px', whiteSpace: 'nowrap'
                  }}>
                    {item.content_type.replace('_', ' ')}
                  </span>
                </div>

                <h3 className="content-title" title={item.title}>{item.title}</h3>

                {/* Extra info */}
                <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#6b7280', margin: '6px 0' }}>
                  {item.chunks_count > 0 && <span>📦 {item.chunks_count} chunks</span>}
                  {item.page_count > 0  && <span>📄 {item.page_count} pages</span>}
                  {item.file_size > 0   && <span>💾 {formatSize(item.file_size)}</span>}
                </div>

                <div className="content-meta">
                  <div className="content-status">
                    {getStatusIcon(item.processing_status)}
                    <span style={{ fontSize: '12px', marginLeft: '4px', textTransform: 'capitalize' }}>
                      {item.processing_status}
                    </span>
                  </div>
                  <span className="content-date" style={{ fontSize: '12px', color: '#9ca3af' }}>
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="content-actions">
                  <button
                    className="action-btn"
                    title="View PDF"
                    onClick={() => handleView(item)}
                    style={{ cursor: 'pointer' }}
                  >
                    <Eye size={15} />
                  </button>
                  <button
                    className="action-btn"
                    title="Download"
                    onClick={() => handleDownload(item)}
                    style={{ cursor: 'pointer' }}
                  >
                    <Download size={15} />
                  </button>
                  <button
                    className="action-btn danger"
                    title="Delete"
                    onClick={() => setDeleteTarget(item)}
                    style={{ cursor: 'pointer' }}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Delete Modal */}
      {deleteTarget && (
        <DeleteModal
          item={deleteTarget}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeleteTarget(null)}
          deleting={deleting}
        />
      )}

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default LibraryTab;