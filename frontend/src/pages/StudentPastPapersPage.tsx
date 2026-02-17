import React, { useState, useEffect, lazy, Suspense } from 'react';
import { 
  FileText, 
  Download, 
  Eye, 
  Calendar, 
  MapPin, 
  Search,
  Filter,
  X,
  BookOpen,
  Award
} from 'lucide-react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import '../styles/StudentPastPapersPage.css';

// ✅ Lazy load PDFViewer — isolates any pdfjs crash from the main page
const PDFViewer = lazy(() => import('../components/PDFViewer'));


interface PastPaper {
  id: string;
  title: string;
  year: number;
  province: string;
  full_marks: number;
  page_count: number;
  file_size: number;
  download_url: string;
  created_at: string;
}

interface Filters {
  years: number[];
  provinces: string[];
}

const StudentPastPapersPage: React.FC = () => {
  const [papers, setPapers] = useState<PastPaper[]>([]);
  const [filters, setFilters] = useState<Filters>({ years: [], provinces: [] });
  const [loading, setLoading] = useState(true);
  
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [viewingPaper, setViewingPaper] = useState<PastPaper | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    loadFilters();
    loadPapers();
  }, [selectedYear, selectedProvince]);

  const loadFilters = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/admin/past-papers/filters');
      // ✅ FIX: guard against API returning unexpected shape
      setFilters({
        years:     Array.isArray(response.data?.years)     ? response.data.years     : [],
        provinces: Array.isArray(response.data?.provinces) ? response.data.provinces : [],
      });
    } catch (error) {
      console.error('Error loading filters:', error);
      // ✅ FIX: keep safe defaults on error — don't leave state undefined
      setFilters({ years: [], provinces: [] });
    }
  };

  const loadPapers = async () => {
    setLoading(true);
    try {
      let url = 'http://localhost:8000/api/v1/admin/past-papers/list';
      const params = new URLSearchParams();
      if (selectedYear) params.append('year', selectedYear.toString());
      if (selectedProvince) params.append('province', selectedProvince);
      if (params.toString()) url += `?${params.toString()}`;
      const response = await axios.get(url);
      setPapers(response.data.papers || []);
    } catch (error) {
      console.error('Error loading papers:', error);
    } finally {
      setLoading(false);
    }
  };

 const handleDownload = async (paper: PastPaper) => {
  try {
    // ✅ FIXED: Proper blob download with correct headers
    const response = await axios.get(
      `http://localhost:8000${paper.download_url}`,
      {
        responseType: 'blob',
        headers: {
          'Accept': 'application/pdf'
        }
      }
    );
    
    // Create blob URL
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    
    // Create download link
    const link = document.createElement('a');
    link.href = url;
    link.download = `${paper.title}.pdf`;
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    console.log('✅ Download successful');
  } catch (error) {
    console.error('❌ Download error:', error);
    alert('Failed to download. Please try again.');
  }
};

  const clearFilters = () => {
    setSelectedYear(null);
    setSelectedProvince(null);
    setSearchQuery('');
  };

  const filteredPapers = papers.filter(paper => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        paper.title.toLowerCase().includes(query) ||
        paper.province.toLowerCase().includes(query) ||
        paper.year.toString().includes(query)
      );
    }
    return true;
  });

  // ✅ FIX: skip papers with missing year to prevent NaN key crash
  const papersByYear = filteredPapers.reduce((acc, paper) => {
    if (!paper.year) return acc;
    if (!acc[paper.year]) acc[paper.year] = [];
    acc[paper.year].push(paper);
    return acc;
  }, {} as Record<number, PastPaper[]>);

  const formatFileSize = (bytes: number) => (bytes / (1024 * 1024)).toFixed(2) + ' MB';

  const activeFiltersCount = (selectedYear ? 1 : 0) + (selectedProvince ? 1 : 0);

  return (
    // ✅ Outer wrapper mirrors ChatPage: flex row, full height
    <div className="past-papers-page-container">
      <Sidebar />                                     {/* ✅ ADDED — same as ChatPage */}

      <main className="past-papers-main">

        {/* Hero Header */}
        <div className="hero-header">
          <div className="hero-content">
            <div className="hero-icon">
              <Award size={48} />
            </div>
            <div className="hero-text">
              <h1>📚 SEE Past Papers</h1>
              <p>Practice with real exam papers from all provinces</p>
            </div>
          </div>
          <div className="hero-stats">
            <div className="stat-badge">
              <FileText size={20} />
              <span>{papers.length} Papers</span>
            </div>
            <div className="stat-badge">
              <Calendar size={20} />
              <span>{filters.years.length} Years</span>
            </div>
            <div className="stat-badge">
              <MapPin size={20} />
              <span>{filters.provinces.length} Provinces</span>
            </div>
          </div>
        </div>

        {/* Search & Filters Bar */}
        <div className="controls-bar">
          <div className="search-box">
            <Search size={20} />
            <input
              type="text"
              placeholder="Search by year, province, or title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="clear-search" onClick={() => setSearchQuery('')}>
                <X size={16} />
              </button>
            )}
          </div>
          <button
            className={`filters-btn ${showFilters ? 'active' : ''}`}
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter size={20} />
            Filters
            {activeFiltersCount > 0 && (
              <span className="filter-count">{activeFiltersCount}</span>
            )}
          </button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="filters-panel">
            <div className="filter-group">
              <label>Year</label>
              <select
                value={selectedYear || ''}
                onChange={(e) => setSelectedYear(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">All Years</option>
                {filters.years.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
            <div className="filter-group">
              <label>Province</label>
              <select
                value={selectedProvince || ''}
                onChange={(e) => setSelectedProvince(e.target.value || null)}
              >
                <option value="">All Provinces</option>
                {filters.provinces.map(province => (
                  <option key={province} value={province}>{province}</option>
                ))}
              </select>
            </div>
            {activeFiltersCount > 0 && (
              <button className="clear-filters-btn" onClick={clearFilters}>
                <X size={16} />
                Clear Filters
              </button>
            )}
          </div>
        )}

        {/* Papers Content */}
        <div className="papers-content">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner" />
              <p>Loading past papers...</p>
            </div>
          ) : filteredPapers.length === 0 ? (
            <div className="empty-state">
              <BookOpen size={64} />
              <h3>No papers found</h3>
              <p>Try adjusting your filters or search query</p>
              {activeFiltersCount > 0 && (
                <button className="btn-primary" onClick={clearFilters}>
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <div className="papers-list">
              {Object.keys(papersByYear)
                .sort((a, b) => Number(b) - Number(a))
                .map(year => (
                  <div key={year} className="year-section">
                    <div className="year-header">
                      <Calendar size={24} />
                      <h2>SEE {year}</h2>
                      <span className="year-count">
                        {(papersByYear[Number(year)] || []).length} paper{(papersByYear[Number(year)] || []).length !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <div className="papers-grid">
                      {(papersByYear[Number(year)] || []).map(paper => (
                        <div key={paper.id} className="paper-card">
                          <div className="paper-card-header">
                            <div className="paper-icon">
                              <FileText size={32} />
                            </div>
                            <div className="paper-badge">{paper.full_marks} marks</div>
                          </div>
                          <div className="paper-card-body">
                            <h3>{paper.province} Province</h3>
                            <div className="paper-meta">
                              <div className="meta-item">
                                <MapPin size={14} />
                                <span>{paper.province}</span>
                              </div>
                              <div className="meta-item">
                                <FileText size={14} />
                                <span>{paper.page_count || '?'} pages</span>
                              </div>
                              <div className="meta-item">
                                <Download size={14} />
                                <span>{formatFileSize(paper.file_size)}</span>
                              </div>
                            </div>
                          </div>
                          <div className="paper-card-actions">
                            <button
                              className="btn-action view-btn"
                              onClick={() => setViewingPaper(paper)}
                            >
                              <Eye size={18} />
                              View Paper
                            </button>
                            <button
                              className="btn-action download-btn"
                              onClick={() => handleDownload(paper)}
                            >
                              <Download size={18} />
                              Download
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>

      </main>

      {/* PDF Viewer Modal — wrapped in Suspense for lazy loading */}
      {viewingPaper && (
        <Suspense fallback={null}>
          <PDFViewer
            paper={viewingPaper}
            onClose={() => setViewingPaper(null)}
            onDownload={() => handleDownload(viewingPaper)}
          />
        </Suspense>
      )}
    </div>
  );
};

export default StudentPastPapersPage;