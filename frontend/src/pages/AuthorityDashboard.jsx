import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, TrendingUp, Users, Zap, Building2, Filter, CheckCircle, Clock, XCircle } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ComposedChart, Line, Area,
} from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import LiveSimulatorModal from '../components/LiveSimulatorModal';
import api from '../services/api';
import toast from 'react-hot-toast';

const DEPT_DATA = [
  { dept: 'CS', highRisk: 18, avgScore: 42, students: 180 },
  { dept: 'ECE', highRisk: 12, avgScore: 36, students: 150 },
  { dept: 'Mech', highRisk: 22, avgScore: 48, students: 160 },
  { dept: 'Civil', highRisk: 9, avgScore: 31, students: 120 },
  { dept: 'IT', highRisk: 14, avgScore: 38, students: 140 },
  { dept: 'EEE', highRisk: 16, avgScore: 40, students: 130 },
];

const RADAR_DATA = [
  { subject: 'Attendance', A: 72, fullMark: 100 },
  { subject: 'CGPA', A: 68, fullMark: 100 },
  { subject: 'Assignments', A: 75, fullMark: 100 },
  { subject: 'Wellbeing', A: 55, fullMark: 100 },
  { subject: 'Engagement', A: 63, fullMark: 100 },
  { subject: 'Mental Health', A: 58, fullMark: 100 },
];

const MONTHLY_DATA = [
  { month: 'Jan', interventions: 12, resolved: 8 },
  { month: 'Feb', interventions: 18, resolved: 14 },
  { month: 'Mar', interventions: 24, resolved: 19 },
  { month: 'Apr', interventions: 31, resolved: 22 },
  { month: 'May', interventions: 27, resolved: 25 },
  { month: 'Jun', interventions: 35, resolved: 28 },
  { month: 'Jul', interventions: 29, resolved: 24 },
];

const INTERVENTIONS = [
  { student: 'Ravi Kumar', dept: 'CS', score: 82, status: 'pending', date: '2024-07-20', action: 'Academic Probation', tier: 4 },
  { student: 'Meena Sharma', dept: 'Mech', score: 76, status: 'in-progress', date: '2024-07-18', action: 'Counselor Referral', tier: 3 },
  { student: 'Arjun Iyer', dept: 'ECE', score: 74, status: 'resolved', date: '2024-07-15', action: 'Parent Meeting', tier: 3 },
  { student: 'Priya Desai', dept: 'IT', score: 71, status: 'pending', date: '2024-07-22', action: 'Financial Aid Review', tier: 2 },
  { student: 'Suresh Nair', dept: 'CS', score: 79, status: 'in-progress', date: '2024-07-19', action: 'Academic Counseling', tier: 3 },
  { student: 'Kavya Rao', dept: 'Civil', score: 73, status: 'resolved', date: '2024-07-14', action: 'Leave of Absence', tier: 4 },
];

const PENDING_ACTIONS_INITIAL = [
  { id: 'ACT-001', student: 'Ravi Kumar', tier: 4, type: 'INSTITUTIONAL_AUTHORITY_ALERT', msg: 'Recommend institutional review for acute depression risk framework.', date: 'Just now' },
  { id: 'ACT-002', student: 'Amit Joshi', tier: 3, type: 'TEACHER_NOTIFICATION', msg: 'Drafted notification to assigned faculty advisor.', date: '2 hrs ago' },
];

const STATUS_ICONS = {
  pending: { icon: Clock, color: '#f59e0b' },
  'in-progress': { icon: TrendingUp, color: '#6366f1' },
  resolved: { icon: CheckCircle, color: '#10b981' },
};

const RISK_COLORS = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#10b981' };

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div style={{
        background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(99,102,241,0.3)',
        borderRadius: '10px', padding: '12px 16px', fontSize: '12px',
      }}>
        <p style={{ color: '#f1f5f9', fontWeight: '600', marginBottom: '6px' }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color || p.stroke, margin: '2px 0' }}>{p.name}: {p.value}</p>
        ))}
      </div>
    );
  }
  return null;
};

export default function AuthorityDashboard() {
  const { user } = useAuth();
  const [showSimulator, setShowSimulator] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [filter, setFilter] = useState('all');
  const [notifications, setNotifications] = useState([]);
  const [pendingActions, setPendingActions] = useState(PENDING_ACTIONS_INITIAL);

  const handleApprove = (id) => {
    setPendingActions(prev => prev.filter(a => a.id !== id));
    toast.success('Action approved and logged to audit_log.jsonl');
  };

  const handleReject = (id) => {
    setPendingActions(prev => prev.filter(a => a.id !== id));
    toast.error('Action rejected.');
  };

  useEffect(() => {
    if (!user?.isDemo) {
      api.get('/notifications/analytics').then(r => setAnalytics(r.data)).catch(() => {});
      api.get('/notifications').then(r => setNotifications(r.data.notifications || [])).catch(() => {});
    }
  }, [user]);

  const totalStudents = DEPT_DATA.reduce((s, d) => s + d.students, 0);
  const totalHighRisk = analytics?.highRisk || DEPT_DATA.reduce((s, d) => s + d.highRisk, 0);

  const filteredInterventions = filter === 'all'
    ? INTERVENTIONS
    : INTERVENTIONS.filter(i => i.status === filter);

  return (
    <div className="page-container">
      <Header onOpenSimulator={() => setShowSimulator(true)} />

      <main className="main-content">
        {/* Header */}
        <div className="animate-fade-in" style={{ marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h1 style={{ fontSize: '26px', fontWeight: '800', color: '#f1f5f9', fontFamily: 'Space Grotesk, sans-serif', margin: 0 }}>
                Authority Dashboard
              </h1>
              <p style={{ color: '#64748b', fontSize: '14px', margin: '4px 0 0' }}>
                Institution-wide risk analytics & intervention tracking
              </p>
            </div>
            <button onClick={() => setShowSimulator(true)} className="btn btn-primary" id="authority-open-simulator">
              <Zap size={16} /> AI Simulator
            </button>
          </div>
        </div>

        {/* KPI Row */}
        <div className="grid-4 animate-fade-in" style={{ marginBottom: '24px' }}>
          {[
            { label: 'Total Students', value: totalStudents, icon: '🏫', color: '#6366f1', sub: 'Across all depts' },
            { label: 'High Risk', value: totalHighRisk, icon: '🚨', color: '#ef4444', sub: 'Need intervention' },
            { label: 'Resolved Cases', value: analytics?.resolved || 24, icon: '✅', color: '#10b981', sub: 'This semester' },
            { label: 'Avg Risk Score', value: `${analytics?.avgScore || 39.2}`, icon: '📈', color: '#f59e0b', sub: 'Institution-wide' },
          ].map(({ label, value, icon, color, sub }) => (
            <div key={label} className="stat-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '22px' }}>{icon}</span>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color, boxShadow: `0 0 8px ${color}` }} />
              </div>
              <div style={{ fontSize: '28px', fontWeight: '800', color, fontFamily: 'Space Grotesk, sans-serif', lineHeight: 1 }}>{value}</div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{label}</div>
              <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px' }}>{sub}</div>
            </div>
          ))}
        </div>

        <div className="grid-2 animate-fade-in" style={{ marginBottom: '24px' }}>
          {/* Dept-wise bar chart */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div className="section-header">
              <div>
                <div className="section-title">High-Risk Students by Department</div>
                <div className="section-subtitle">Distribution across departments</div>
              </div>
              <Building2 size={18} color="#6366f1" />
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={DEPT_DATA} barSize={14}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                <XAxis dataKey="dept" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="highRisk" name="High Risk Students" fill="url(#barGrad)" radius={[6, 6, 0, 0]}>
                  <defs>
                    <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" />
                      <stop offset="100%" stopColor="#dc2626" stopOpacity={0.7} />
                    </linearGradient>
                  </defs>
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Radar chart — institutional profile */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div className="section-header">
              <div>
                <div className="section-title">Institutional Wellness Profile</div>
                <div className="section-subtitle">Average scores across dimensions</div>
              </div>
              <Shield size={18} color="#6366f1" />
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <RadarChart data={RADAR_DATA}>
                <PolarGrid stroke="rgba(99,102,241,0.15)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar
                  name="Score"
                  dataKey="A"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Monthly Intervention Trend */}
        <div className="glass-card animate-fade-in" style={{ padding: '24px', marginBottom: '24px' }}>
          <div className="section-header">
            <div>
              <div className="section-title">Intervention Tracking — Monthly</div>
              <div className="section-subtitle">Cases raised vs. resolved this academic year</div>
            </div>
            <TrendingUp size={18} color="#6366f1" />
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={MONTHLY_DATA}>
              <defs>
                <linearGradient id="intGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area dataKey="interventions" name="Cases Raised" stroke="#6366f1" fill="url(#intGrad)" strokeWidth={2} />
              <Line type="monotone" dataKey="resolved" name="Resolved" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 4 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* AI Guardrails Inbox */}
        <div className="glass-card animate-fade-in" style={{ padding: '24px', marginBottom: '24px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <div className="section-header">
            <div>
              <div className="section-title" style={{color: '#f87171'}}>AI Guardrails Inbox (Human-in-the-Loop)</div>
              <div className="section-subtitle">Pending AI actions requiring authority sign-off before sending</div>
            </div>
            <Shield size={18} color="#ef4444" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {pendingActions.length === 0 ? (
              <div style={{color: '#94a3b8', fontSize: '13px', textAlign: 'center', padding: '16px'}}>No pending actions in your queue.</div>
            ) : pendingActions.map(act => (
              <div key={act.id} style={{
                background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '10px',
                border: '1px solid rgba(245, 158, 11, 0.3)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
              }}>
                <div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                    <span className="badge badge-high">Tier {act.tier}</span>
                    <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#e2e8f0' }}>{act.type}</span>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>• {act.date}</span>
                  </div>
                  <div style={{ fontSize: '14px', color: '#94a3b8' }}>
                    <span style={{ color: '#fff' }}>[{act.student}]:</span> {act.msg}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-primary btn-sm" style={{ background: '#10b981', borderColor: '#10b981' }} onClick={() => handleApprove(act.id)}>
                    <CheckCircle size={14} /> Approve
                  </button>
                  <button className="btn btn-secondary btn-sm" style={{ color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)' }} onClick={() => handleReject(act.id)}>
                    <XCircle size={14} /> Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 4-Tier Triage Center (Intervention Table) */}
        <div className="glass-card animate-fade-in" style={{ padding: '24px' }}>
          <div className="section-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <div className="section-title">4-Tier Triage Center</div>
              <div className="section-subtitle">Categorized student risk escalation levels</div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              {['all', 'pending', 'in-progress', 'resolved'].map(f => (
                <button
                  key={f}
                  id={`filter-${f}`}
                  onClick={() => setFilter(f)}
                  style={{
                    padding: '5px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                    background: filter === f ? 'rgba(99,102,241,0.2)' : 'transparent',
                    border: `1px solid ${filter === f ? 'rgba(99,102,241,0.4)' : 'rgba(99,102,241,0.12)'}`,
                    color: filter === f ? '#a78bfa' : '#64748b',
                    transition: 'all 0.2s',
                    textTransform: 'capitalize',
                  }}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Department</th>
                  <th>Risk Score</th>
                  <th>Tier</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Intervention</th>
                </tr>
              </thead>
              <tbody>
                {filteredInterventions.map((item, i) => {
                  const { icon: StatusIcon, color } = STATUS_ICONS[item.status];
                  return (
                    <tr key={i}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div style={{
                            width: '32px', height: '32px', borderRadius: '8px',
                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '13px', fontWeight: '700', color: 'white',
                          }}>
                            {item.student.charAt(0)}
                          </div>
                          <span style={{ fontWeight: '600' }}>{item.student}</span>
                        </div>
                      </td>
                      <td>
                        <span className="badge badge-student">{item.dept}</span>
                      </td>
                      <td>
                        <span style={{
                          fontWeight: '800', fontFamily: 'Space Grotesk, sans-serif', fontSize: '18px',
                          color: item.score >= 70 ? '#ef4444' : item.score >= 40 ? '#f59e0b' : '#10b981',
                        }}>
                          {item.score}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge-${item.tier === 4 ? 'high' : item.tier === 3 ? 'medium' : 'student'}`}>Tier {item.tier}</span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <StatusIcon size={14} color={color} />
                          <span style={{ fontSize: '12px', color, fontWeight: '600', textTransform: 'capitalize' }}>{item.status}</span>
                        </div>
                      </td>
                      <td style={{ color: '#64748b', fontSize: '12px' }}>{item.date}</td>
                      <td style={{ color: '#94a3b8', fontSize: '13px' }}>{item.action}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {showSimulator && <LiveSimulatorModal onClose={() => setShowSimulator(false)} />}
    </div>
  );
}
