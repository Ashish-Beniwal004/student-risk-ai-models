import { useState, useEffect } from 'react';
import { Users, AlertTriangle, TrendingDown, TrendingUp, Zap, BookOpen } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, AreaChart, Area,
} from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import LiveSimulatorModal from '../components/LiveSimulatorModal';
import api from '../services/api';

// Demo data for class risk distribution
const CLASS_RISK_DATA = [
  { name: 'Data Structures', high: 4, medium: 12, low: 34 },
  { name: 'OS', high: 8, medium: 15, low: 27 },
  { name: 'DBMS', high: 2, medium: 9, low: 39 },
  { name: 'Networks', high: 11, medium: 18, low: 21 },
  { name: 'Soft. Eng.', high: 5, medium: 14, low: 31 },
];

const TREND_DATA = [
  { week: 'Wk 1', avgRisk: 22 },
  { week: 'Wk 2', avgRisk: 28 },
  { week: 'Wk 3', avgRisk: 25 },
  { week: 'Wk 4', avgRisk: 34 },
  { week: 'Wk 5', avgRisk: 31 },
  { week: 'Wk 6', avgRisk: 38 },
  { week: 'Wk 7', avgRisk: 35 },
  { week: 'Wk 8', avgRisk: 42 },
];

const AT_RISK_STUDENTS = [
  { name: 'Ravi Kumar', subject: 'Networks', score: 78, level: 'HIGH', trend: 'up' },
  { name: 'Sneha Patel', subject: 'OS', score: 71, level: 'HIGH', trend: 'up' },
  { name: 'Amit Joshi', subject: 'Soft. Eng.', score: 64, level: 'MEDIUM', trend: 'down' },
  { name: 'Divya Nair', subject: 'Data Struct.', score: 58, level: 'MEDIUM', trend: 'stable' },
  { name: 'Kiran Rao', subject: 'DBMS', score: 52, level: 'MEDIUM', trend: 'down' },
];

const PIE_DATA = [
  { name: 'LOW', value: 62, color: '#10b981' },
  { name: 'MEDIUM', value: 27, color: '#f59e0b' },
  { name: 'HIGH', value: 11, color: '#ef4444' },
];

const RISK_COLORS = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#10b981' };

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(99,102,241,0.3)',
        borderRadius: '10px', padding: '12px 16px', fontSize: '12px',
      }}>
        <p style={{ color: '#f1f5f9', fontWeight: '600', marginBottom: '6px' }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color, margin: '2px 0' }}>{p.name}: {p.value}</p>
        ))}
      </div>
    );
  }
  return null;
};

export default function TeacherDashboard() {
  const { user } = useAuth();
  const [showSimulator, setShowSimulator] = useState(false);
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (!user?.isDemo) {
      api.get('/notifications/analytics').then(r => setAnalytics(r.data)).catch(() => {});
    }
  }, [user]);

  const totalStudents = 100;

  return (
    <div className="page-container">
      <Header onOpenSimulator={() => setShowSimulator(true)} />

      <main className="main-content">
        {/* Header */}
        <div className="animate-fade-in" style={{ marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h1 style={{ fontSize: '26px', fontWeight: '800', color: '#f1f5f9', fontFamily: 'Space Grotesk, sans-serif', margin: 0 }}>
                Teacher Dashboard
              </h1>
              <p style={{ color: '#64748b', fontSize: '14px', margin: '4px 0 0' }}>
                {user?.department} · Class overview & at-risk monitoring
              </p>
            </div>
            <button onClick={() => setShowSimulator(true)} className="btn btn-primary" id="teacher-open-simulator">
              <Zap size={16} /> AI Simulator
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid-4 animate-fade-in" style={{ marginBottom: '24px' }}>
          {[
            { label: 'Total Students', value: analytics?.total || totalStudents, icon: '👥', color: '#6366f1', sub: 'In your classes' },
            { label: 'High Risk', value: analytics?.highRisk || 11, icon: '🚨', color: '#ef4444', sub: 'Need immediate help' },
            { label: 'Medium Risk', value: analytics?.medRisk || 27, icon: '⚠️', color: '#f59e0b', sub: 'Monitor closely' },
            { label: 'Avg Risk Score', value: `${analytics?.avgScore || 32.4}`, icon: '📊', color: '#10b981', sub: 'Class average' },
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
          {/* Risk Distribution Bar Chart */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div className="section-header">
              <div>
                <div className="section-title">Risk Distribution by Subject</div>
                <div className="section-subtitle">Student count per risk level</div>
              </div>
              <BookOpen size={18} color="#6366f1" />
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={CLASS_RISK_DATA} barSize={10} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                <Bar dataKey="high" name="High Risk" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="medium" name="Medium Risk" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="low" name="Low Risk" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Pie Chart */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div className="section-header">
              <div>
                <div className="section-title">Overall Risk Breakdown</div>
                <div className="section-subtitle">Class-wide distribution</div>
              </div>
              <Users size={18} color="#6366f1" />
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={PIE_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                  labelLine={false}
                >
                  {PIE_DATA.map((entry, index) => (
                    <Cell key={index} fill={entry.color} style={{ filter: `drop-shadow(0 0 6px ${entry.color}60)` }} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weekly Risk Trend */}
        <div className="glass-card animate-fade-in" style={{ padding: '24px', marginBottom: '24px' }}>
          <div className="section-header">
            <div>
              <div className="section-title">Weekly Average Risk Trend</div>
              <div className="section-subtitle">Class risk score over time</div>
            </div>
            <TrendingUp size={18} color="#6366f1" />
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={TREND_DATA}>
              <defs>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
              <XAxis dataKey="week" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} domain={[0, 60]} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="avgRisk" name="Avg Risk Score" stroke="#6366f1" strokeWidth={2.5} fill="url(#riskGrad)" dot={{ fill: '#6366f1', r: 4 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* At-Risk Students Table */}
        <div className="glass-card animate-fade-in" style={{ padding: '24px' }}>
          <div className="section-header">
            <div>
              <div className="section-title">At-Risk Students</div>
              <div className="section-subtitle">Students requiring immediate attention</div>
            </div>
            <AlertTriangle size={18} color="#f59e0b" />
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Subject</th>
                  <th>Risk Score</th>
                  <th>Risk Level</th>
                  <th>Trend</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {AT_RISK_STUDENTS.map((student, i) => (
                  <tr key={i}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{
                          width: '32px', height: '32px', borderRadius: '8px',
                          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '13px', fontWeight: '700', color: 'white',
                        }}>
                          {student.name.charAt(0)}
                        </div>
                        <span style={{ fontWeight: '600' }}>{student.name}</span>
                      </div>
                    </td>
                    <td style={{ color: '#94a3b8' }}>{student.subject}</td>
                    <td>
                      <span style={{ fontWeight: '700', color: RISK_COLORS[student.level], fontFamily: 'Space Grotesk, sans-serif', fontSize: '16px' }}>
                        {student.score}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge-${student.level.toLowerCase()}`}>{student.level}</span>
                    </td>
                    <td>
                      {student.trend === 'up' ? <TrendingUp size={16} color="#ef4444" /> :
                       student.trend === 'down' ? <TrendingDown size={16} color="#10b981" /> :
                       <span style={{ color: '#64748b', fontSize: '12px' }}>stable</span>}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        id={`contact-student-${i}`}
                        onClick={() => alert(`Contact feature coming soon for ${student.name}`)}
                      >
                        Contact
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {showSimulator && <LiveSimulatorModal onClose={() => setShowSimulator(false)} />}
    </div>
  );
}
