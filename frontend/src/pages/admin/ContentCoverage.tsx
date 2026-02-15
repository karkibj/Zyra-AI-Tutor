import React, { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { adminApi, type ContentCoverageResponse } from '../../services/adminApi';
import '../../styles/ContentCoverage.css';

const ContentCoverage: React.FC = () => {
  const [coverage, setCoverage] = useState<ContentCoverageResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedChapter, setSelectedChapter] = useState<ContentCoverageResponse | null>(null);
  
  // SEE Mathematics Syllabus (CDC Curriculum)
  const syllabusTopics: Record<string, string[]> = {
    algebra: [
      'Linear Equations',
      'Quadratic Equations',
      'Quadratic Formula',
      'Discriminant',
      'Factorization',
      'Polynomials',
      'Simultaneous Equations'
    ],
    geometry: [
      'Triangles',
      'Circles',
      'Quadrilaterals',
      'Coordinate Geometry',
      'Constructions',
      'Similarity',
      'Congruence'
    ],
    trigonometry: [
      'Trigonometric Ratios',
      'Angles of Elevation and Depression',
      'Heights and Distances',
      'Trigonometric Identities',
      'Right Triangle Applications'
    ],
    statistics: [
      'Mean, Median, Mode',
      'Range and Deviation',
      'Frequency Distribution',
      'Graphs and Charts',
      'Data Interpretation'
    ],
    probability: [
      'Basic Probability',
      'Events and Outcomes',
      'Theoretical Probability',
      'Experimental Probability',
      'Combined Probability'
    ],
    mensuration: [
      'Area and Perimeter',
      'Surface Area',
      'Volume',
      'Prisms and Pyramids',
      'Cylinders and Cones',
      'Spheres'
    ]
  };

  useEffect(() => {
    loadCoverage();
  }, []);

  const loadCoverage = async () => {
    setIsLoading(true);
    try {
      const data = await adminApi.getContentCoverage();
      setCoverage(data);
    } catch (error) {
      console.error('Failed to load coverage:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getCoverageColor = (percentage: number): string => {
    if (percentage >= 80) return 'coverage-excellent';
    if (percentage >= 60) return 'coverage-good';
    if (percentage >= 40) return 'coverage-moderate';
    return 'coverage-poor';
  };

  const getMissingTopics = (chapter: string, coveredTopics: string[]): string[] => {
    const allTopics = syllabusTopics[chapter.toLowerCase()] || [];
    return allTopics.filter(topic => 
      !coveredTopics.some(covered => 
        covered.toLowerCase().includes(topic.toLowerCase())
      )
    );
  };

  const getOverallCoverage = (): number => {
    if (coverage.length === 0) return 0;
    const total = coverage.reduce((sum, c) => sum + c.coverage_percentage, 0);
    return Math.round(total / coverage.length);
  };

  return (
    <AdminLayout>
      <div className="content-coverage">
        <div className="cc-header">
          <div>
            <h1>📊 Content Coverage Analysis</h1>
            <p className="cc-subtitle">
              Track curriculum coverage against CDC SEE Mathematics syllabus
            </p>
          </div>
          <div className="cc-overall">
            <div className="overall-score">
              <div className="score-circle">
                <span className="score-value">{getOverallCoverage()}%</span>
                <span className="score-label">Overall</span>
              </div>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="cc-loading">
            <div className="loading-spinner"></div>
            <p>Analyzing content coverage...</p>
          </div>
        ) : (
          <>
            {/* Coverage Grid */}
            <div className="coverage-grid">
              {coverage.map(item => (
                <div 
                  key={item.chapter}
                  className={`coverage-card ${getCoverageColor(item.coverage_percentage)}`}
                  onClick={() => setSelectedChapter(item)}
                >
                  <div className="cc-card-header">
                    <h3>{item.chapter}</h3>
                    <span className="cc-percentage">
                      {Math.round(item.coverage_percentage)}%
                    </span>
                  </div>
                  
                  <div className="cc-progress-bar">
                    <div 
                      className="cc-progress-fill"
                      style={{ width: `${item.coverage_percentage}%` }}
                    ></div>
                  </div>
                  
                  <div className="cc-card-stats">
                    <div className="cc-stat">
                      <span className="cc-stat-icon">📄</span>
                      <span className="cc-stat-value">{item.document_count}</span>
                      <span className="cc-stat-label">Documents</span>
                    </div>
                    <div className="cc-stat">
                      <span className="cc-stat-icon">📝</span>
                      <span className="cc-stat-value">{item.chunk_count}</span>
                      <span className="cc-stat-label">Chunks</span>
                    </div>
                    <div className="cc-stat">
                      <span className="cc-stat-icon">🏷️</span>
                      <span className="cc-stat-value">{item.topics_covered.length}</span>
                      <span className="cc-stat-label">Topics</span>
                    </div>
                  </div>
                  
                  <button className="cc-view-details">
                    View Details →
                  </button>
                </div>
              ))}
            </div>

            {/* Syllabus Checklist */}
            <div className="syllabus-checklist">
              <h2>📋 SEE Syllabus Coverage Checklist</h2>
              
              {Object.entries(syllabusTopics).map(([chapter, topics]) => {
                const chapterCoverage = coverage.find(c => c.chapter.toLowerCase() === chapter);
                const coveredTopics = chapterCoverage?.topics_covered || [];
                const missingTopics = getMissingTopics(chapter, coveredTopics);
                
                return (
                  <div key={chapter} className="checklist-chapter">
                    <div className="checklist-header">
                      <h3>{chapter.charAt(0).toUpperCase() + chapter.slice(1)}</h3>
                      <span className="checklist-progress">
                        {topics.length - missingTopics.length} / {topics.length} covered
                      </span>
                    </div>
                    
                    <div className="checklist-topics">
                      {topics.map(topic => {
                        const isCovered = !missingTopics.includes(topic);
                        return (
                          <div 
                            key={topic}
                            className={`checklist-item ${isCovered ? 'checked' : 'unchecked'}`}
                          >
                            <span className="checklist-icon">
                              {isCovered ? '✅' : '⬜'}
                            </span>
                            <span className="checklist-topic">{topic}</span>
                          </div>
                        );
                      })}
                    </div>
                    
                    {missingTopics.length > 0 && (
                      <div className="checklist-alert">
                        <span className="alert-icon">⚠️</span>
                        <span className="alert-text">
                          {missingTopics.length} topic(s) need content
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Recommendations */}
            <div className="coverage-recommendations">
              <h2>💡 Content Recommendations</h2>
              
              <div className="recommendations-list">
                {coverage
                  .filter(c => c.coverage_percentage < 80)
                  .map(item => {
                    const missingTopics = getMissingTopics(item.chapter, item.topics_covered);
                    return (
                      <div key={item.chapter} className="recommendation-card">
                        <div className="rec-header">
                          <span className="rec-chapter">{item.chapter}</span>
                          <span className="rec-priority">
                            {item.coverage_percentage < 40 ? '🔴 High Priority' : 
                             item.coverage_percentage < 60 ? '🟡 Medium Priority' : 
                             '🟢 Low Priority'}
                          </span>
                        </div>
                        <p className="rec-message">
                          Upload content covering: {missingTopics.slice(0, 3).join(', ')}
                          {missingTopics.length > 3 && ` and ${missingTopics.length - 3} more`}
                        </p>
                      </div>
                    );
                  })}
                
                {coverage.every(c => c.coverage_percentage >= 80) && (
                  <div className="rec-success">
                    <span className="success-icon">🎉</span>
                    <p>Excellent! All chapters have good coverage.</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Chapter Detail Modal */}
        {selectedChapter && (
          <div className="modal-overlay" onClick={() => setSelectedChapter(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>{selectedChapter.chapter} - Detailed Coverage</h2>
                <button className="modal-close" onClick={() => setSelectedChapter(null)}>
                  ✖
                </button>
              </div>
              
              <div className="modal-body">
                <div className="detail-stats">
                  <div className="detail-stat">
                    <span className="detail-value">{selectedChapter.document_count}</span>
                    <span className="detail-label">Documents</span>
                  </div>
                  <div className="detail-stat">
                    <span className="detail-value">{selectedChapter.chunk_count}</span>
                    <span className="detail-label">Content Chunks</span>
                  </div>
                  <div className="detail-stat">
                    <span className="detail-value">{Math.round(selectedChapter.coverage_percentage)}%</span>
                    <span className="detail-label">Coverage</span>
                  </div>
                </div>
                
                <div className="detail-section">
                  <h3>Covered Topics:</h3>
                  <div className="topics-grid">
                    {selectedChapter.topics_covered.map(topic => (
                      <span key={topic} className="topic-badge topic-covered">
                        ✓ {topic}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="detail-section">
                  <h3>Missing Topics:</h3>
                  <div className="topics-grid">
                    {getMissingTopics(selectedChapter.chapter, selectedChapter.topics_covered).map(topic => (
                      <span key={topic} className="topic-badge topic-missing">
                        ✗ {topic}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="modal-footer">
                <button className="btn btn-primary" onClick={() => setSelectedChapter(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
};

export default ContentCoverage;