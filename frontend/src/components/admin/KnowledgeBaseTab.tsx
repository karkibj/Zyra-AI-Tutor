import React, { useState, useEffect } from 'react';
import { Database, RefreshCw, AlertTriangle, CheckCircle, AlertCircle, BookOpen } from 'lucide-react';

interface ChapterStat {
  name: string;
  code: string;
  see_marks: number;
  chunk_count: number;
  health: 'good' | 'moderate' | 'low';
}

interface KBStats {
  total_vectors: number;
  total_tagged: number;
  total_untagged: number;
  by_content_type: Record<string, number>;
  chapters: ChapterStat[];
  garbled_chunks: number;
  index_size_mb: number;
  error?: string;
}

const API = 'http://localhost:8000/api/v1';

export const KnowledgeBaseTab: React.FC = () => {
  const [stats, setStats]     = useState<KBStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  useEffect(() => { fetchStats(); }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/admin/knowledge-base/stats`);
      const data = await res.json();
      setStats(data);
      setLastRefresh(new Date());
    } catch (e) {
      setStats({ error: 'Failed to fetch', total_vectors: 0, total_tagged: 0, total_untagged: 0, by_content_type: {}, chapters: [], garbled_chunks: 0, index_size_mb: 0 });
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (health: string) => {
    if (health === 'good')     return '#10b981';
    if (health === 'moderate') return '#f59e0b';
    return '#ef4444';
  };

  const getHealthBg = (health: string) => {
    if (health === 'good')     return '#d1fae5';
    if (health === 'moderate') return '#fef3c7';
    return '#fee2e2';
  };

  const getHealthLabel = (health: string, count: number) => {
    if (count === 0) return 'No data';
    if (health === 'good')     return 'Good';
    if (health === 'moderate') return 'Moderate';
    return 'Low';
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem', gap: '12px', color: '#6b7280' }}>
        <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite' }} />
        <span>Reading vector store...</span>
      </div>
    );
  }

  if (!stats || stats.error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
        <AlertCircle size={40} style={{ margin: '0 auto 12px' }} />
        <p>Could not load knowledge base stats. Make sure backend is running.</p>
      </div>
    );
  }

  const taggedPct = stats.total_vectors > 0 ? Math.round((stats.total_tagged / stats.total_vectors) * 100) : 0;
  const totalSEEMarks = stats.chapters.reduce((s, c) => s + c.see_marks, 0);
  const goodChapters = stats.chapters.filter(c => c.health === 'good').length;

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: '#111827' }}>Knowledge Base</h2>
          <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#6b7280' }}>
            Vector store health — what Zyra knows for each CDC chapter
            {lastRefresh && <span> · Last updated {lastRefresh.toLocaleTimeString()}</span>}
          </p>
        </div>
        <button
          onClick={fetchStats}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '14px', cursor: 'pointer' }}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        {[
          { label: 'Total vectors', value: stats.total_vectors, icon: Database, color: '#6366f1', bg: '#eef2ff' },
          { label: 'Chapter-tagged', value: `${stats.total_tagged} (${taggedPct}%)`, icon: CheckCircle, color: '#10b981', bg: '#d1fae5' },
          { label: 'Chapters covered', value: `${goodChapters} / 15`, icon: BookOpen, color: '#f59e0b', bg: '#fef3c7' },
          { label: 'Index size', value: `${stats.index_size_mb} MB`, icon: Database, color: '#3b82f6', bg: '#dbeafe' },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '1rem' }}>
            <div style={{ width: '36px', height: '36px', background: bg, borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '8px' }}>
              <Icon size={18} color={color} />
            </div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: '#111827' }}>{value}</div>
            <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '2px' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Content type breakdown */}
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '1.25rem' }}>
        <h3 style={{ margin: '0 0 12px', fontSize: '15px', fontWeight: 600, color: '#111827' }}>By content type</h3>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {Object.entries(stats.by_content_type).map(([type, count]) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '8px 14px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#374151' }}>{count}</span>
              <span style={{ fontSize: '13px', color: '#6b7280' }}>{type.replace('_', ' ')}</span>
            </div>
          ))}
          {stats.garbled_chunks > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: '8px', padding: '8px 14px' }}>
              <AlertTriangle size={14} color="#ef4444" />
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#dc2626' }}>{stats.garbled_chunks} garbled</span>
              <span style={{ fontSize: '13px', color: '#6b7280' }}>model question chunks</span>
            </div>
          )}
        </div>
      </div>

      {/* Chapter-by-chapter breakdown */}
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: '#111827' }}>Chapter knowledge coverage</h3>
          <span style={{ fontSize: '13px', color: '#6b7280' }}>SEE Total: {totalSEEMarks} marks</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                {['Chapter', 'Code', 'SEE marks', 'Chunks', 'Health', 'Coverage'].map(h => (
                  <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600, whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {stats.chapters.map((ch, i) => {
                const barWidth = Math.min((ch.chunk_count / 70) * 100, 100);
                return (
                  <tr key={ch.code} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 500, color: '#111827' }}>{ch.name}</td>
                    <td style={{ padding: '10px 12px', color: '#6b7280', fontFamily: 'monospace', fontSize: '12px' }}>{ch.code}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <span style={{ background: '#eef2ff', color: '#4f46e5', padding: '2px 8px', borderRadius: '99px', fontWeight: 600 }}>{ch.see_marks}</span>
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'center', fontWeight: 600, color: ch.chunk_count === 0 ? '#ef4444' : '#111827' }}>
                      {ch.chunk_count}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{ background: getHealthBg(ch.health), color: getHealthColor(ch.health), padding: '2px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: 600 }}>
                        {getHealthLabel(ch.health, ch.chunk_count)}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', minWidth: '120px' }}>
                      <div style={{ background: '#f3f4f6', borderRadius: '99px', height: '6px', overflow: 'hidden' }}>
                        <div style={{ width: `${barWidth}%`, height: '100%', background: getHealthColor(ch.health), borderRadius: '99px', transition: 'width 0.3s' }} />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '20px', marginTop: '16px', padding: '12px', background: '#f9fafb', borderRadius: '8px' }}>
          {[
            { label: 'Good (30+ chunks)', color: '#10b981', bg: '#d1fae5' },
            { label: 'Moderate (10–29)', color: '#f59e0b', bg: '#fef3c7' },
            { label: 'Low (<10 chunks)', color: '#ef4444', bg: '#fee2e2' },
          ].map(({ label, color, bg }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: color, display: 'inline-block' }} />
              <span style={{ color: '#374151' }}>{label}</span>
            </div>
          ))}
          <div style={{ marginLeft: 'auto', fontSize: '12px', color: '#6b7280' }}>
            Max bar = 70 chunks (Area & Volume)
          </div>
        </div>
      </div>

    </div>
  );
};

export default KnowledgeBaseTab;