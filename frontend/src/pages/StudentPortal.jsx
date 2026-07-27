import { useState } from 'react';
import { Activity, TrendingUp, Award, BookOpen, Zap, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import LiveSimulatorModal from '../components/LiveSimulatorModal';

const DEMO_METRICS = {
  attendance: 78,
  gpa: 7.4,
  assignmentCompletion: 82,
  midtermScore: 68,
  riskScore: 34,
  riskLevel: 'MEDIUM',
};

const COURSE_DATA = [
  { name: 'Data Structures', grade: 'B+', attendance: 88, status: 'good' },
  { name: 'Operating Systems', grade: 'C+', attendance: 71, status: 'warn' },
  { name: 'Database Management', grade: 'A-', attendance: 92, status: 'good' },
  { name: 'Computer Networks', grade: 'C', attendance: 65, status: 'danger' },
  { name: 'Software Engineering', grade: 'B', attendance: 80, status: 'good' },
];

const STATUS_COLORS = { good: '#10b981', warn: '#f59e0b', danger: '#ef4444' };

function MetricBar({ label, value, max = 100, color, unit = '%' }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
        <span style={{ fontSize: '13px', color: '#94a3b8' }}>{label}</span>
        <span style={{ fontSize: '14px', fontWeight: '700', color: color }}>{value}{unit}</span>
      </div>
      <div style={{ height: '6px', background: 'rgba(99, 102, 241, 0.12)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${(value / max) * 100}%`,
          background: `linear-gradient(90deg, ${color}99, ${color})`,
          borderRadius: '3px',
          transition: 'width 1s ease',
          boxShadow: `0 0 8px ${color}60`,
        }} />
      </div>
    </div>
  );
}

export default function StudentPortal() {
  const { user } = useAuth();
  const [showSimulator, setShowSimulator] = useState(false);

  const metrics = DEMO_METRICS;
  const riskColor = metrics.riskLevel === 'HIGH' ? '#ef4444' : metrics.riskLevel === 'MEDIUM' ? '#f59e0b' : '#10b981';

  return (
    <div className="page-container">
      <Header onOpenSimulator={() => setShowSimulator(true)} />

      <main className="main-content">
        {/* Page Header */}
        <div className="animate-fade-in" style={{ marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h1 style={{ fontSize: '26px', fontWeight: '800', color: '#f1f5f9', fontFamily: 'Space Grotesk, sans-serif', margin: 0 }}>
                Welcome back, {user?.name?.split(' ')[0]} 👋
              </h1>
              <p style={{ color: '#64748b', fontSize: '14px', margin: '4px 0 0' }}>
                {user?.department} · {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}
              </p>
            </div>
            <button
              onClick={() => setShowSimulator(true)}
              className="btn btn-primary"
              id="portal-open-simulator"
            >
              <Zap size={16} />
              Run AI Assessment
            </button>
          </div>
        </div>

        {/* Risk Banner */}
        <div className="animate-fade-in" style={{
          background: `linear-gradient(135deg, rgba(${
            metrics.riskLevel === 'HIGH' ? '239,68,68' :
            metrics.riskLevel === 'MEDIUM' ? '245,158,11' : '16,185,129'
          }, 0.08), rgba(15,23,42,0.6))`,
          border: `1px solid ${riskColor}30`,
          borderRadius: '16px',
          padding: '20px 24px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          flexWrap: 'wrap',
        }}>
          <div style={{
            width: '52px', height: '52px', borderRadius: '14px', flexShrink: 0,
            background: `rgba(${metrics.riskLevel === 'HIGH' ? '239,68,68' : metrics.riskLevel === 'MEDIUM' ? '245,158,11' : '16,185,129'}, 0.15)`,
            border: `1px solid ${riskColor}40`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {metrics.riskLevel === 'LOW' ? <CheckCircle color={riskColor} size={24} /> : <AlertTriangle color={riskColor} size={24} />}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '16px', fontWeight: '700', color: '#f1f5f9', marginBottom: '2px' }}>
              Your current risk score is&nbsp;
              <span style={{ color: riskColor }}>{metrics.riskScore}/100</span>
              &nbsp;—&nbsp;
              <span style={{ color: riskColor }}>{metrics.riskLevel} RISK</span>
            </div>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
              {metrics.riskLevel === 'LOW' && 'Keep up the great work! Your academic performance is excellent.'}
              {metrics.riskLevel === 'MEDIUM' && 'Some areas need attention. Consider speaking with your advisor.'}
              {metrics.riskLevel === 'HIGH' && 'Immediate intervention recommended. Please contact your teacher.'}
            </p>
          </div>
          <div style={{
            fontSize: '36px', fontWeight: '900', color: riskColor,
            fontFamily: 'Space Grotesk, sans-serif',
            textShadow: `0 0 20px ${riskColor}60`,
          }}>
            {metrics.riskScore}
          </div>
        </div>

        {/* Stat Cards */}
        <div className="grid-4 animate-fade-in" style={{ marginBottom: '24px' }}>
          {[
            { label: 'Attendance', value: `${metrics.attendance}%`, icon: '📅', color: '#6366f1', sub: 'This semester' },
            { label: 'CGPA', value: metrics.gpa.toFixed(1), icon: '🎯', color: '#8b5cf6', sub: 'Out of 10.0' },
            { label: 'Assignments', value: `${metrics.assignmentCompletion}%`, icon: '📝', color: '#c084fc', sub: 'Submitted on time' },
            { label: 'Midterm Avg', value: `${metrics.midtermScore}%`, icon: '📊', color: '#a78bfa', sub: 'Across all subjects' },
          ].map(({ label, value, icon, color, sub }) => (
            <div key={label} className="stat-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <span style={{ fontSize: '22px' }}>{icon}</span>
                <div style={{
                  width: '8px', height: '8px', borderRadius: '50%',
                  background: color, boxShadow: `0 0 8px ${color}`,
                }} />
              </div>
              <div style={{ fontSize: '28px', fontWeight: '800', color, fontFamily: 'Space Grotesk, sans-serif', lineHeight: 1 }}>{value}</div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{label}</div>
              <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px' }}>{sub}</div>
            </div>
          ))}
        </div>

        <div className="grid-2 animate-fade-in">
          {/* Performance Metrics */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div className="section-header">
              <div>
                <div className="section-title">Performance Metrics</div>
                <div className="section-subtitle">Current semester overview</div>
              </div>
              <Activity size={18} color="#6366f1" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <MetricBar label="Attendance Rate" value={metrics.attendance} color="#6366f1" />
              <MetricBar label="CGPA" value={metrics.gpa} max={10} color="#8b5cf6" unit="/10" />
              <MetricBar label="Assignment Completion" value={metrics.assignmentCompletion} color="#c084fc" />
              <MetricBar label="Midterm Score" value={metrics.midtermScore} color="#a78bfa" />
            </div>
          </div>

          {/* Course-wise Status */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div className="section-header">
              <div>
                <div className="section-title">Course Performance</div>
                <div className="section-subtitle">Subject-level breakdown</div>
              </div>
              <BookOpen size={18} color="#6366f1" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {COURSE_DATA.map(course => (
                <div key={course.name} style={{
                  display: 'flex', alignItems: 'center', gap: '12px',
                  padding: '12px 14px',
                  background: 'rgba(15, 23, 42, 0.5)',
                  borderRadius: '10px',
                  border: `1px solid ${STATUS_COLORS[course.status]}20`,
                }}>
                  <div style={{
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: STATUS_COLORS[course.status],
                    boxShadow: `0 0 8px ${STATUS_COLORS[course.status]}`,
                    flexShrink: 0,
                  }} />
                  <div style={{ flex: 1, fontSize: '13px', color: '#e2e8f0', fontWeight: '500' }}>{course.name}</div>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>{course.attendance}% attend.</span>
                    <span style={{
                      fontSize: '13px', fontWeight: '700',
                      color: STATUS_COLORS[course.status],
                      padding: '2px 8px', borderRadius: '6px',
                      background: `${STATUS_COLORS[course.status]}15`,
                    }}>
                      {course.grade}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recommendations */}
        <div className="glass-card animate-fade-in" style={{ padding: '24px', marginTop: '24px' }}>
          <div className="section-header">
            <div>
              <div className="section-title">AI Recommendations</div>
              <div className="section-subtitle">Personalized intervention suggestions</div>
            </div>
            <Zap size={18} color="#6366f1" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            {[
              { tip: 'Improve attendance in Computer Networks to avoid academic risk', icon: '⚠️', urgency: 'high' },
              { tip: 'Complete pending assignments before the weekend deadline', icon: '📝', urgency: 'medium' },
              { tip: 'Schedule a meeting with your academic advisor', icon: '👤', urgency: 'medium' },
              { tip: 'Consider joining study groups for better concept retention', icon: '👥', urgency: 'low' },
            ].map((rec, i) => (
              <div key={i} style={{
                padding: '14px 16px',
                background: 'rgba(15, 23, 42, 0.6)',
                borderRadius: '10px',
                border: `1px solid rgba(${rec.urgency === 'high' ? '239,68,68' : rec.urgency === 'medium' ? '245,158,11' : '16,185,129'}, 0.2)`,
                display: 'flex', gap: '10px', alignItems: 'flex-start',
              }}>
                <span style={{ fontSize: '18px', flexShrink: 0 }}>{rec.icon}</span>
                <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>{rec.tip}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {showSimulator && <LiveSimulatorModal onClose={() => setShowSimulator(false)} />}
    </div>
  );
}
