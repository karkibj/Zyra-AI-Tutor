import React, { useState, useEffect } from 'react';
import { Users, RefreshCw, Shield, GraduationCap, MessageSquare, BookOpen, CheckCircle, XCircle, Chrome } from 'lucide-react';

interface UserData {
  id: string;
  email: string;
  full_name: string;
  role: string;
  provider: string;
  is_active: boolean;
  chat_count: number;
  topics_practiced: number;
  created_at: string | null;
}

interface UsersResponse {
  total: number;
  students: number;
  admins: number;
  users: UserData[];
}

const API = 'http://localhost:8000/api/v1';

export const StudentsTab: React.FC = () => {
  const [data, setData]       = useState<UsersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter]   = useState<'all' | 'student' | 'admin'>('all');
  const [search, setSearch]   = useState('');

  useEffect(() => { fetchUsers(); }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/admin/users/list`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error('Failed to load users', e);
    } finally {
      setLoading(false);
    }
  };

  const filtered = (data?.users || []).filter(u => {
    const matchRole   = filter === 'all' || u.role === filter;
    const matchSearch = u.full_name.toLowerCase().includes(search.toLowerCase()) ||
                        u.email.toLowerCase().includes(search.toLowerCase());
    return matchRole && matchSearch;
  });

  const getRoleBadge = (role: string) => {
    if (role === 'admin') return (
      <span style={{ display:'inline-flex', alignItems:'center', gap:'4px', background:'#fef3c7', color:'#92400e', padding:'2px 10px', borderRadius:'99px', fontSize:'12px', fontWeight:600 }}>
        <Shield size={11} /> Admin
      </span>
    );
    return (
      <span style={{ display:'inline-flex', alignItems:'center', gap:'4px', background:'#dbeafe', color:'#1e40af', padding:'2px 10px', borderRadius:'99px', fontSize:'12px', fontWeight:600 }}>
        <GraduationCap size={11} /> Student
      </span>
    );
  };

  const getProviderBadge = (provider: string) => {
    if (provider === 'google') return (
      <span style={{ display:'inline-flex', alignItems:'center', gap:'4px', background:'#fee2e2', color:'#991b1b', padding:'2px 8px', borderRadius:'99px', fontSize:'11px' }}>
        <Chrome size={10} /> Google
      </span>
    );
    return (
      <span style={{ background:'#f3f4f6', color:'#374151', padding:'2px 8px', borderRadius:'99px', fontSize:'11px' }}>
        Local
      </span>
    );
  };

  const getInitials = (name: string) =>
    name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'numeric' });
  };

  if (loading) return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', padding:'3rem', gap:'10px', color:'#6b7280' }}>
      <RefreshCw size={18} style={{ animation:'spin 1s linear infinite' }} />
      Loading users...
    </div>
  );

  return (
    <div style={{ padding:'1.5rem', display:'flex', flexDirection:'column', gap:'1.5rem' }}>

      {/* Header */}
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
        <div>
          <h2 style={{ margin:0, fontSize:'20px', fontWeight:600, color:'#111827' }}>Students & Users</h2>
          <p style={{ margin:'4px 0 0', fontSize:'14px', color:'#6b7280' }}>All registered users on Zyra</p>
        </div>
        <button onClick={fetchUsers} style={{ display:'flex', alignItems:'center', gap:'6px', padding:'8px 16px', background:'#6366f1', color:'#fff', border:'none', borderRadius:'8px', fontSize:'14px', cursor:'pointer' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:'12px' }}>
        {[
          { label:'Total users',  value: data?.total || 0,    icon: Users,          bg:'#eef2ff', color:'#6366f1' },
          { label:'Students',     value: data?.students || 0, icon: GraduationCap,  bg:'#dbeafe', color:'#1d4ed8' },
          { label:'Admins',       value: data?.admins || 0,   icon: Shield,         bg:'#fef3c7', color:'#d97706' },
          { label:'Total chats',  value: (data?.users || []).reduce((s,u) => s + u.chat_count, 0), icon: MessageSquare, bg:'#d1fae5', color:'#059669' },
        ].map(({ label, value, icon: Icon, bg, color }) => (
          <div key={label} style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:'12px', padding:'1rem' }}>
            <div style={{ width:'36px', height:'36px', background:bg, borderRadius:'8px', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'8px' }}>
              <Icon size={18} color={color} />
            </div>
            <div style={{ fontSize:'22px', fontWeight:700, color:'#111827' }}>{value}</div>
            <div style={{ fontSize:'13px', color:'#6b7280', marginTop:'2px' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display:'flex', gap:'10px', alignItems:'center' }}>
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ flex:1, padding:'8px 14px', border:'1px solid #d1d5db', borderRadius:'8px', fontSize:'14px', outline:'none' }}
        />
        {(['all','student','admin'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding:'8px 16px', borderRadius:'8px', fontSize:'13px', fontWeight:500, cursor:'pointer',
            background: filter === f ? '#6366f1' : '#f3f4f6',
            color: filter === f ? '#fff' : '#374151',
            border: filter === f ? 'none' : '1px solid #e5e7eb'
          }}>
            {f === 'all' ? 'All' : f === 'student' ? 'Students' : 'Admins'}
          </button>
        ))}
      </div>

      {/* Users table */}
      <div style={{ background:'#fff', border:'1px solid #e5e7eb', borderRadius:'12px', overflow:'hidden' }}>
        <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'13px' }}>
          <thead>
            <tr style={{ borderBottom:'2px solid #e5e7eb', background:'#f9fafb' }}>
              {['User', 'Role', 'Provider', 'Chats', 'Topics Practiced', 'Status', 'Joined'].map(h => (
                <th key={h} style={{ padding:'10px 16px', textAlign:'left', color:'#6b7280', fontWeight:600, whiteSpace:'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding:'2rem', textAlign:'center', color:'#9ca3af' }}>No users found</td>
              </tr>
            ) : filtered.map((user, i) => (
              <tr key={user.id} style={{ borderBottom:'1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                <td style={{ padding:'12px 16px' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
                    <div style={{
                      width:'36px', height:'36px', borderRadius:'50%',
                      background:'#e0e7ff', display:'flex', alignItems:'center', justifyContent:'center',
                      fontSize:'13px', fontWeight:700, color:'#4338ca', flexShrink:0
                    }}>
                      {getInitials(user.full_name)}
                    </div>
                    <div>
                      <div style={{ fontWeight:500, color:'#111827' }}>{user.full_name}</div>
                      <div style={{ fontSize:'12px', color:'#6b7280' }}>{user.email}</div>
                    </div>
                  </div>
                </td>
                <td style={{ padding:'12px 16px' }}>{getRoleBadge(user.role)}</td>
                <td style={{ padding:'12px 16px' }}>{getProviderBadge(user.provider)}</td>
                <td style={{ padding:'12px 16px' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'4px', color: user.chat_count > 0 ? '#111827' : '#9ca3af', fontWeight: user.chat_count > 0 ? 600 : 400 }}>
                    <MessageSquare size={13} />
                    {user.chat_count}
                  </div>
                </td>
                <td style={{ padding:'12px 16px' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'4px', color: user.topics_practiced > 0 ? '#111827' : '#9ca3af' }}>
                    <BookOpen size={13} />
                    {user.topics_practiced} topic{user.topics_practiced !== 1 ? 's' : ''}
                  </div>
                </td>
                <td style={{ padding:'12px 16px' }}>
                  {user.is_active
                    ? <span style={{ display:'inline-flex', alignItems:'center', gap:'4px', color:'#059669', fontSize:'12px', fontWeight:600 }}><CheckCircle size={13} /> Active</span>
                    : <span style={{ display:'inline-flex', alignItems:'center', gap:'4px', color:'#dc2626', fontSize:'12px', fontWeight:600 }}><XCircle size={13} /> Inactive</span>
                  }
                </td>
                <td style={{ padding:'12px 16px', color:'#6b7280', fontSize:'12px' }}>{formatDate(user.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding:'10px 16px', borderTop:'1px solid #f3f4f6', fontSize:'12px', color:'#9ca3af' }}>
          Showing {filtered.length} of {data?.total || 0} users
        </div>
      </div>

    </div>
  );
};

export default StudentsTab;