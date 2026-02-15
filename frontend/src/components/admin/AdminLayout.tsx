import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../../styles/AdminLayout.css';

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="admin-layout">
      {/* Sidebar */}
      <aside className="admin-sidebar">
        <div className="sidebar-header">
          <h1 className="sidebar-logo">
            <span className="logo-icon"></span>
            Zyra Admin
          </h1>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${isActive('/admin') || isActive('/admin/dashboard') ? 'nav-item-active' : ''}`}
            onClick={() => navigate('/admin/dashboard')}
          >
            <span className="nav-icon">📊</span>
            <span className="nav-label">Dashboard</span>
          </button>

         <button
            className={`nav-item ${isActive('/admin/documents') ? 'nav-item-active' : ''}`}
            onClick={() => navigate('/admin/documents')}
          >
            <span className="nav-icon">📚</span>
            <span className="nav-label">Document Management</span>
          </button>

          <button
            className={`nav-item ${isActive('/admin/coverage') ? 'nav-item-active' : ''}`}
            onClick={() => navigate('/admin/coverage')}
          >
            <span className="nav-icon">📊</span>
            <span className="nav-label">Content Coverage</span>
          </button>

          <div className="nav-divider"></div>

          <button
            className="nav-item"
            onClick={() => window.open('http://localhost:8000/docs', '_blank')}
          >
            <span className="nav-icon">📖</span>
            <span className="nav-label">API Docs</span>
          </button>

          <button
            className="nav-item"
            onClick={() => navigate('/dashboard')}
          >
            <span className="nav-icon">👨‍🎓</span>
            <span className="nav-label">Student View</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="admin-info">
            <div className="admin-avatar">👤</div>
            <div className="admin-details">
              <div className="admin-name">Admin</div>
              <div className="admin-role">System Administrator</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="admin-main">
        <div className="admin-content">
          {children}
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;