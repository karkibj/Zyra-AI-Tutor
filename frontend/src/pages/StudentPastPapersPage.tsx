import React, { useState, useEffect, lazy, Suspense } from 'react';
import {
  FileText, Download, Eye, Calendar, MapPin, Search,
  Filter, X, BookOpen, Award, ChevronDown, AlertCircle
} from 'lucide-react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import '../styles/StudentPastPapersPage.css';

const PDFViewer = lazy(() => import('../components/PDFViewer'));

// ── Types ─────────────────────────────────────────────────────────────────────
interface PastPaper {
  id: string; title: string; year: number; province: string;
  full_marks: number; page_count: number; file_size: number;
  download_url: string; created_at: string;
}
interface Filters { years: number[]; provinces: string[]; }

// Color palette — one per province slot, assigned by index when filters load.
// No province names hardcoded — all data comes from the backend.
const PROVINCE_COLORS = [
  '#ef4444', '#fb923c', '#fbbf24', '#34d399',
  '#60a5fa', '#a78bfa', '#f472b6',
];

const makeProvinceCfg = (color: string) => ({
  color,
  bg:     `${color}1a`,
  border: `${color}47`,
});

const FALLBACK_COLOR = { color: '#94a3b8', bg: 'rgba(148,163,184,.10)', border: 'rgba(148,163,184,.25)' };

const API  = 'http://localhost:8000/api/v1';
const HOST = 'http://localhost:8000';

const StudentPastPapersPage: React.FC = () => {
  const [papers, setPapers]                     = useState<PastPaper[]>([]);
  const [filters, setFilters]                   = useState<Filters>({ years: [], provinces: [] });
  const [loading, setLoading]                   = useState(true);
  const [selectedYear, setSelectedYear]         = useState<number | null>(null);
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null);
  const [searchQuery, setSearchQuery]           = useState('');
  const [viewingPaper, setViewingPaper]         = useState<PastPaper | null>(null);
  const [showFilters, setShowFilters]           = useState(false);
  const [downloadError, setDownloadError]       = useState<string | null>(null);
  // Province → color map, built when filters load — no hardcoding
  const [provinceColors, setProvinceColors]       = useState<Record<string, ReturnType<typeof makeProvinceCfg>>>({});

  useEffect(() => { loadFilters(); loadPapers(); }, [selectedYear, selectedProvince]);

  const loadFilters = async () => {
    try {
      const r         = await axios.get(`${API}/admin/past-papers/filters`);
      const years     = Array.isArray(r.data?.years)     ? r.data.years     : [];
      const provinces = Array.isArray(r.data?.provinces) ? r.data.provinces : [];
      setFilters({ years, provinces });

      // Assign one color per province by arrival order — no name mapping
      const colorMap: Record<string, ReturnType<typeof makeProvinceCfg>> = {};
      provinces.forEach((p: string, idx: number) => {
        colorMap[p] = makeProvinceCfg(PROVINCE_COLORS[idx % PROVINCE_COLORS.length]);
      });
      setProvinceColors(colorMap);
    } catch {
      setFilters({ years: [], provinces: [] });
    }
  };

  const loadPapers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedYear)     params.append('year',     selectedYear.toString());
      if (selectedProvince) params.append('province', selectedProvince);
      const url = `${API}/admin/past-papers/list${params.toString() ? `?${params}` : ''}`;
      const r   = await axios.get(url);
      setPapers(r.data.papers || []);
    } catch {
      setPapers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (paper: PastPaper) => {
    setDownloadError(null);
    try {
      const r    = await axios.get(`${HOST}${paper.download_url}`, {
        responseType: 'blob',
        headers: { Accept: 'application/pdf' },
      });
      const url  = window.URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href  = url;
      link.download = `${paper.title}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      setDownloadError('Download failed. Please try again.');
      setTimeout(() => setDownloadError(null), 4000);
    }
  };

  const clearFilters = () => { setSelectedYear(null); setSelectedProvince(null); setSearchQuery(''); };

  const filteredPapers = papers.filter(p => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return p.title.toLowerCase().includes(q) || p.province.toLowerCase().includes(q) || p.year.toString().includes(q);
  });

  const papersByYear = filteredPapers.reduce((acc, p) => {
    if (!p.year) return acc;
    if (!acc[p.year]) acc[p.year] = [];
    acc[p.year].push(p);
    return acc;
  }, {} as Record<number, PastPaper[]>);

  const fmt        = (b: number) => (b / (1024 * 1024)).toFixed(2) + ' MB';
  const activeCount = (selectedYear ? 1 : 0) + (selectedProvince ? 1 : 0);

  return (
    <div className="past-papers-page-container">
      <Sidebar />
      <main className="past-papers-main">

        {/* ── Hero ── */}
        <div className="pp-hero">
          <div className="pp-hero-left">
            <div className="pp-hero-icon"><FileText size={24} /></div>
            <div>
              <h1 className="pp-hero-title">SEE Past Papers</h1>
              <p className="pp-hero-subtitle">Real exam papers from all 7 provinces · Practice anytime</p>
            </div>
          </div>
          <div className="pp-stats-row">
            <div className="pp-stat-pill">
              <FileText size={14} />
              <strong>{papers.length}</strong>
              <span>Papers</span>
            </div>
            <div className="pp-stat-divider" />
            <div className="pp-stat-pill">
              <Calendar size={14} />
              <strong>{filters.years.length}</strong>
              <span>Years</span>
            </div>
            <div className="pp-stat-divider" />
            <div className="pp-stat-pill">
              <MapPin size={14} />
              <strong>{filters.provinces.length || 7}</strong>
              <span>Provinces</span>
            </div>
          </div>
        </div>

        {/* ── Download error toast ── */}
        {downloadError && (
          <div className="pp-error-toast">
            <AlertCircle size={15} />
            {downloadError}
          </div>
        )}

        {/* ── Search + filter bar ── */}
        <div className="pp-controls">
          <div className="pp-search-wrapper">
            <Search size={16} className="pp-search-icon" />
            <input
              className="pp-search-input"
              type="text"
              placeholder="Search by year, province…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="pp-search-clear" onClick={() => setSearchQuery('')}>
                <X size={15} />
              </button>
            )}
          </div>

          <button
            className={`pp-filter-btn ${showFilters ? 'active' : ''}`}
            onClick={() => setShowFilters(v => !v)}
          >
            <Filter size={15} />
            Filters
            {activeCount > 0 && <span className="pp-filter-badge">{activeCount}</span>}
            <ChevronDown size={14} className={showFilters ? 'rotate' : ''} />
          </button>

          {activeCount > 0 && (
            <button className="pp-clear-all" onClick={clearFilters}>
              <X size={13} /> Clear
            </button>
          )}
        </div>

        {/* ── Filter panel ── */}
        {showFilters && (
          <div className="pp-filters-panel">
            <div className="pp-filter-group">
              <label className="pp-filter-label">Year</label>
              <select
                className="pp-filter-select"
                value={selectedYear || ''}
                onChange={e => setSelectedYear(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">All Years</option>
                {filters.years.map(y => <option key={y} value={y}>SEE {y}</option>)}
              </select>
            </div>
            <div className="pp-filter-group">
              <label className="pp-filter-label">Province</label>
              <select
                className="pp-filter-select"
                value={selectedProvince || ''}
                onChange={e => setSelectedProvince(e.target.value || null)}
              >
                <option value="">All Provinces</option>
                {filters.provinces.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>
        )}

        {/* ── Papers ── */}
        <div className="pp-content">
          {loading ? (
            <div className="pp-loading">
              <div className="pp-spinner" />
              <p>Loading past papers…</p>
            </div>
          ) : filteredPapers.length === 0 ? (
            <div className="pp-empty">
              <BookOpen size={48} className="pp-empty-icon" />
              <h3 className="pp-empty-title">No papers found</h3>
              <p className="pp-empty-text">Try adjusting your search or filters</p>
              {activeCount > 0 && (
                <button className="pp-empty-btn" onClick={clearFilters}>Clear Filters</button>
              )}
            </div>
          ) : (
            Object.keys(papersByYear)
              .sort((a, b) => Number(b) - Number(a))
              .map(year => (
                <div key={year} className="pp-year-section">
                  <div className="pp-year-header">
                    <div className="pp-year-title">
                      <Calendar size={18} />
                      <h2>SEE {year}</h2>
                    </div>
                    <span className="pp-year-count">
                      {papersByYear[Number(year)].length} paper{papersByYear[Number(year)].length !== 1 ? 's' : ''}
                    </span>
                  </div>

                  <div className="pp-papers-grid">
                    {papersByYear[Number(year)].map(paper => {
                      const cfg = provinceColors[paper.province] ?? FALLBACK_COLOR;
                      return (
                        <div
                          key={paper.id}
                          className="pp-paper-card"
                          style={{
                            '--province-color':  cfg.color,
                            '--province-bg':     cfg.bg,
                            '--province-border': cfg.border,
                          } as React.CSSProperties}
                        >
                          <div className="pp-card-body">
                            {/* Province badge */}
                            <div
                              className="pp-province-badge"
                              style={{ background: cfg.bg, borderColor: cfg.border, color: cfg.color }}
                            >
                              <MapPin size={12} />
                              {paper.province}
                            </div>

                            <h3 className="pp-card-title">{paper.province} Province</h3>

                            <div className="pp-card-meta">
                              <span className="pp-meta-item">
                                <Award size={13} />{paper.full_marks} marks
                              </span>
                              <span className="pp-meta-item">
                                <FileText size={13} />{paper.page_count || '?'} pages
                              </span>
                              <span className="pp-meta-item">
                                <Download size={13} />{fmt(paper.file_size)}
                              </span>
                            </div>
                          </div>

                          <div className="pp-card-actions">
                            <button className="pp-view-btn" onClick={() => setViewingPaper(paper)}>
                              <Eye size={15} /> View
                            </button>
                            <button className="pp-download-btn" onClick={() => handleDownload(paper)}>
                              <Download size={15} /> Download
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
          )}
        </div>
      </main>

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