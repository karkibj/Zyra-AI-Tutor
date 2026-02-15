import React from 'react';
import { TrendingUp, AlertTriangle, CheckCircle, BarChart3 } from 'lucide-react';

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

interface AnalyticsTabProps {
  coverage: CoverageData | null;
}

export const AnalyticsTab: React.FC<AnalyticsTabProps> = ({ coverage }) => {
  if (!coverage) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  const excellentChapters = coverage.coverage.filter(c => c.status === 'excellent').length;
  const goodChapters = coverage.coverage.filter(c => c.status === 'good').length;
  const needsAttention = coverage.coverage.filter(c => c.status === 'needs_attention').length;

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <div>
          <h2>Analytics Dashboard</h2>
          <p>Comprehensive coverage analysis and insights</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="analytics-summary">
        <div className="analytics-card excellent">
          <CheckCircle className="card-icon" />
          <div className="card-content">
            <h3>{excellentChapters}</h3>
            <p>Excellent Coverage</p>
            <span className="card-detail">80%+ resources</span>
          </div>
        </div>

        <div className="analytics-card good">
          <TrendingUp className="card-icon" />
          <div className="card-content">
            <h3>{goodChapters}</h3>
            <p>Good Coverage</p>
            <span className="card-detail">60-79% resources</span>
          </div>
        </div>

        <div className="analytics-card warning">
          <AlertTriangle className="card-icon" />
          <div className="card-content">
            <h3>{needsAttention}</h3>
            <p>Needs Attention</p>
            <span className="card-detail">Below 60%</span>
          </div>
        </div>

        <div className="analytics-card info">
          <BarChart3 className="card-icon" />
          <div className="card-content">
            <h3>{coverage.summary.total_resources}</h3>
            <p>Total Resources</p>
            <span className="card-detail">Across {coverage.summary.total_chapters} chapters</span>
          </div>
        </div>
      </div>

      {/* Detailed Table */}
      <div className="analytics-table-container">
        <h3>Chapter-wise Coverage Analysis</h3>
        <div className="analytics-table-wrapper">
          <table className="analytics-table">
            <thead>
              <tr>
                <th>Ch #</th>
                <th>Chapter Name</th>
                <th>Resources</th>
                <th>Coverage</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {coverage.coverage.map((chapter) => (
                <tr key={chapter.chapter_number}>
                  <td className="chapter-num">{chapter.chapter_number}</td>
                  <td className="chapter-name-cell">{chapter.chapter_name}</td>
                  <td className="resource-count">{chapter.total_resources}</td>
                  <td className="coverage-cell">
                    <div className="mini-progress">
                      <div 
                        className={`mini-progress-fill ${chapter.status}`}
                        style={{ width: `${chapter.coverage_score}%` }}
                      ></div>
                    </div>
                    <span className="coverage-percent">{chapter.coverage_score}%</span>
                  </td>
                  <td>
                    <span className={`status-badge ${chapter.status}`}>
                      {chapter.status.replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsTab;