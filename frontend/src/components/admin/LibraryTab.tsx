import React, { useState, useEffect } from 'react';
import { Search, Filter, Eye, Download, Trash2, FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  content_type: string;
  file_path: string;
  processing_status: string;
  created_at: string;
}

export const LibraryTab: React.FC = () => {
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    fetchContent();
  }, [filterType, filterStatus]);

  const fetchContent = async () => {
    setLoading(true);
    try {
      let url = 'http://localhost:8000/api/v1/admin/content/list?limit=100';
      
      if (filterType !== 'all') {
        url += `&content_type=${filterType}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      setContent(data.items || []);
    } catch (error) {
      console.error('Error fetching content:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredContent = content.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || item.processing_status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="status-icon success" />;
      case 'processing':
        return <Clock className="status-icon warning" />;
      case 'failed':
        return <AlertCircle className="status-icon error" />;
      default:
        return <Clock className="status-icon muted" />;
    }
  };

  const getContentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      curriculum: 'purple',
      past_paper: 'indigo',
      model_question: 'blue',
      solution: 'green',
      explanation: 'amber',
      teacher_note: 'pink'
    };
    return colors[type] || 'gray';
  };

  return (
    <div className="library-container">
      {/* Header */}
      <div className="library-header">
        <div>
          <h2>Content Library</h2>
          <p>Browse and manage all uploaded content</p>
        </div>
        <button className="btn btn-primary" onClick={fetchContent}>
          Refresh
        </button>
      </div>

      {/* Filters & Search */}
      <div className="library-filters">
        <div className="search-box">
          <Search className="search-icon" />
          <input
            type="text"
            placeholder="Search content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <Filter size={18} />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Types</option>
            <option value="curriculum">Curriculum</option>
            <option value="past_paper">Past Papers</option>
            <option value="model_question">Model Questions</option>
            <option value="solution">Solutions</option>
            <option value="explanation">Explanations</option>
            <option value="teacher_note">Teacher Notes</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="library-stats">
        <div className="stat-item">
          <span className="stat-label">Total</span>
          <span className="stat-value">{content.length}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Completed</span>
          <span className="stat-value success">
            {content.filter(c => c.processing_status === 'completed').length}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Processing</span>
          <span className="stat-value warning">
            {content.filter(c => c.processing_status === 'processing').length}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Pending</span>
          <span className="stat-value muted">
            {content.filter(c => c.processing_status === 'pending').length}
          </span>
        </div>
      </div>

      {/* Content Grid */}
      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
        </div>
      ) : filteredContent.length === 0 ? (
        <div className="empty-state">
          <FileText size={64} className="empty-icon" />
          <h3>No content found</h3>
          <p>Try adjusting your filters or upload new content</p>
        </div>
      ) : (
        <div className="content-grid">
          {filteredContent.map((item) => (
            <div key={item.id} className="content-card">
              <div className="content-card-header">
                <FileText className="content-icon" />
                <span className={`content-badge ${getContentTypeColor(item.content_type)}`}>
                  {item.content_type.replace('_', ' ')}
                </span>
              </div>
              
              <h3 className="content-title">{item.title}</h3>
              
              <div className="content-meta">
                <div className="content-status">
                  {getStatusIcon(item.processing_status)}
                  <span>{item.processing_status}</span>
                </div>
                <span className="content-date">
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>

              <div className="content-actions">
                <button className="action-btn" title="View">
                  <Eye size={16} />
                </button>
                <button className="action-btn" title="Download">
                  <Download size={16} />
                </button>
                <button className="action-btn danger" title="Delete">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LibraryTab;