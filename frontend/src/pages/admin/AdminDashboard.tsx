import React, { useState, useEffect } from 'react';
import {
  Upload,
  FileText,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Clock,
  BarChart3,
  FolderTree,
  FileQuestion,
  Plus,
  Search,
  Filter,
  Download,
  Eye,
  Settings,
  Inbox,
  Users
} from 'lucide-react';
import '../../styles/AdminDashboard.css'
import UploadTab from '../../components/admin/UploadTab';
import AnalyticsTab from '../../components/admin/AnalyticsTab';
import LibraryTab from '../../components/admin/LibraryTab';
import CurriculumTab from '../../components/admin/CurriculumTab';
import PastPapersTab from '../../components/admin/PastPapersTab';
import KnowledgeBaseTab from '../../components/admin/KnowledgeBaseTab';
import StudentsTab from '../../components/admin/Studentstab';

interface DashboardStats {
  total_content: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  recent_uploads: Array<{
    id: string;
    title: string;
    content_type: string;
    created_at: string;
  }>;
  processing_queue: number;
}

interface CoverageData {
  summary: {
    total_chapters: number;
    total_resources: number;
    chapters_needing_attention: number;
  };
  coverage: Array<{
    chapter_name: string;
    chapter_number: number;
    total_resources: number;
    coverage_score: number;
    status: string;
  }>;
}

const AdminDashboard: React.FC = () => {
  const [showSettings, setShowSettings] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'upload' | 'library' | 'curriculum' | 'analytics' | 'past-papers' | 'knowledge-base' | 'students'>('overview');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [coverage, setCoverage] = useState<CoverageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, coverageRes] = await Promise.all([
        fetch('http://localhost:8000/api/v1/admin/dashboard/stats'),
        fetch('http://localhost:8000/api/v1/admin/content/coverage')
      ]);

      const statsData = await statsRes.json();
      const coverageData = await coverageRes.json();

      setStats(statsData);
      setCoverage(coverageData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'upload', label: 'Upload Content', icon: Upload },
    { id: 'library', label: 'Content Library', icon: FileText },
    { id: 'past-papers', label: 'Past Papers', icon: FileQuestion }, 
    { id: 'curriculum', label: 'Curriculum', icon: FolderTree },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'knowledge-base', label: 'Knowledge Base', icon: BarChart3 },
    { id: 'students', label: 'Students', icon: Users }
  ];

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <header className="admin-header">
        <div className="admin-header-content">
          <div className="admin-header-top">
            <div className="admin-branding">
              <div className="admin-logo">Z</div>
              <div className="admin-branding-text">
                <h1>Zyra Admin</h1>
                <p>Content Management System</p>
              </div>
            </div>

            <div className="admin-header-actions">
              <button className="admin-settings-btn" onClick={() => setShowSettings(true)} title="System Settings">
                <Settings />
              </button>
              <div className="admin-avatar">A</div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="admin-nav">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`admin-nav-tab ${activeTab === tab.id ? 'active' : ''}`}
                >
                  <Icon />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="admin-main">
        {activeTab === 'overview' && (
          <OverviewTab 
            stats={stats} 
            coverage={coverage} 
            loading={loading} 
            onRefresh={fetchDashboardData}
            onTabChange={setActiveTab}
          />
        )}
        {activeTab === 'upload' && <UploadTab onUploadComplete={fetchDashboardData} />}
        {activeTab === 'library' && <LibraryTab />}
        {activeTab === 'curriculum' && <CurriculumTab />}
        {activeTab === 'analytics' && <AnalyticsTab coverage={coverage} />}
        {activeTab === 'past-papers' && <PastPapersTab />}
        {activeTab === 'knowledge-base' && <KnowledgeBaseTab />}
        {activeTab === 'students' && <StudentsTab />}
      {/* Settings Dropdown */}
      {showSettings && (
        <>
          {/* Backdrop */}
          <div style={{ position: 'fixed', inset: 0, zIndex: 9998 }} onClick={() => setShowSettings(false)} />
          {/* Dropdown */}
          <div style={{
            position: 'fixed', top: '64px', right: '24px', zIndex: 9999,
            background: '#fff', borderRadius: '12px', padding: '8px',
            boxShadow: '0 8px 30px rgba(0,0,0,0.15)', border: '1px solid #e5e7eb',
            minWidth: '200px'
          }}>
            <button
              onClick={() => { window.open('/home', '_blank'); setShowSettings(false); }}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                padding: '10px 14px', border: 'none', borderRadius: '8px',
                background: 'none', cursor: 'pointer', fontSize: '14px', color: '#374151',
                textAlign: 'left'
              }}
              onMouseEnter={e => (e.currentTarget.style.background = '#f3f4f6')}
              onMouseLeave={e => (e.currentTarget.style.background = 'none')}
            >
              <span style={{ fontSize: '16px' }}>👁️</span>
              View Student Mode
            </button>
            <div style={{ height: '1px', background: '#f3f4f6', margin: '4px 0' }} />
            <button
              onClick={() => { localStorage.removeItem('token'); window.location.href = '/login'; }}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                padding: '10px 14px', border: 'none', borderRadius: '8px',
                background: 'none', cursor: 'pointer', fontSize: '14px', color: '#ef4444',
                textAlign: 'left'
              }}
              onMouseEnter={e => (e.currentTarget.style.background = '#fee2e2')}
              onMouseLeave={e => (e.currentTarget.style.background = 'none')}
            >
              <span style={{ fontSize: '16px' }}>🚪</span>
              Logout
            </button>
          </div>
        </>
      )}
      </main>
    </div>
  );
};

// ============================================================================
// OVERVIEW TAB COMPONENT (FIXED)
// ============================================================================

const OverviewTab: React.FC<{
  stats: DashboardStats | null;
  coverage: CoverageData | null;
  loading: boolean;
  onRefresh: () => void;
  onTabChange: (tab: any) => void;
}> = ({ stats, coverage, loading, onRefresh, onTabChange }) => {
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  const calculateCoveragePercentage = () => {
    if (!coverage) return 0;
    const target = coverage.summary.total_chapters * 20; // 20 resources per chapter target
    const actual = coverage.summary.total_resources;
    return Math.round((actual / target) * 100);
  };

  const hasCoverageData = coverage && coverage.coverage && coverage.coverage.length > 0;
  const hasRecentUploads = stats && stats.recent_uploads && stats.recent_uploads.length > 0;

  return (
    <div>
      {/* Stats Cards */}
      <div className="stats-grid">
        <StatCard
          title="Total Content"
          value={stats?.total_content || 0}
          icon={FileText}
          color="indigo"
          trend="Total documents"
        />
        <StatCard
          title="Processing"
          value={stats?.processing_queue || 0}
          icon={Clock}
          color="amber"
          trend="In queue"
        />
        <StatCard
          title="Chapters"
          value={coverage?.summary.total_chapters || 0}
          icon={FolderTree}
          color="purple"
          trend="All active"
        />
        <StatCard
          title="Coverage Score"
          value={`${calculateCoveragePercentage()}%`}
          icon={TrendingUp}
          color="green"
          trend="Target: 100%"
        />
      </div>

      {/* Coverage Progress */}
      <div className="coverage-section">
        <div className="coverage-header">
          <h2>Curriculum Coverage</h2>
          <button onClick={onRefresh} className="refresh-btn">
            Refresh
          </button>
        </div>

        {hasCoverageData ? (
          <div className="coverage-list">
            {coverage.coverage.slice(0, 5).map((chapter) => (
              <div key={chapter.chapter_number} className="coverage-item">
                <div className="coverage-item-header">
                  <span className="coverage-item-title">
                    Ch {chapter.chapter_number}: {chapter.chapter_name}
                  </span>
                  <span className="coverage-item-count">
                    {chapter.total_resources} resources
                  </span>
                </div>
                <div className="coverage-progress-bar">
                  <div
                    className={`coverage-progress-fill ${chapter.status}`}
                    style={{ width: `${chapter.coverage_score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="section-empty-state">
            <FolderTree />
            <p>No curriculum loaded yet</p>
          </div>
        )}
      </div>

      {/* Recent Uploads & Quick Actions */}
      <div className="two-col-grid">
        {/* Recent Uploads */}
        <div className="recent-section">
          <h2>Recent Uploads</h2>
          {hasRecentUploads ? (
            <div className="recent-list">
              {stats.recent_uploads.map((upload) => (
                <div key={upload.id} className="recent-item">
                  <div className="recent-item-icon">
                    <FileText />
                  </div>
                  <div className="recent-item-content">
                    <div className="recent-item-title">{upload.title}</div>
                    <div className="recent-item-date">
                      {new Date(upload.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <span className="recent-item-badge">
                    {upload.content_type}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="section-empty-state">
              <Inbox />
              <p>No uploads yet. Start by uploading content!</p>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="quick-actions-section">
          <h2>Quick Actions</h2>
          <div className="quick-actions-grid">
            <QuickActionButton icon={Upload} label="Upload Content" onClick={() => onTabChange('upload')} />
            <QuickActionButton icon={FileText} label="View Library" onClick={() => onTabChange('library')} />
            <QuickActionButton icon={BarChart3} label="Knowledge Base" onClick={() => onTabChange('knowledge-base')} />
            <QuickActionButton icon={TrendingUp} label="Analytics" onClick={() => onTabChange('analytics')} />
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// STAT CARD COMPONENT
// ============================================================================

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: any;
  color: string;
  trend: string;
}> = ({ title, value, icon: Icon, color, trend }) => {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <div className={`stat-card-icon ${color}`}>
          <Icon />
        </div>
      </div>
      <div className="stat-card-value">{value}</div>
      <div className="stat-card-label">{title}</div>
      <div className="stat-card-trend">{trend}</div>
    </div>
  );
};

// ============================================================================
// QUICK ACTION BUTTON COMPONENT
// ============================================================================

const QuickActionButton: React.FC<{
  icon: any;
  label: string;
  onClick?: () => void;
}> = ({ icon: Icon, label, onClick }) => {
  return (
    <button className="quick-action-btn" onClick={onClick}>
      <Icon />
      <span>{label}</span>
    </button>
  );
};

export default AdminDashboard;