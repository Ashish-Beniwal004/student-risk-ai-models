import { useState } from 'react';
import { X, Zap, AlertTriangle, TrendingDown, Activity, BookOpen, BarChart2 } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import RiskGauge from './RiskGauge';

const INITIAL = {
  attendance: 75,
  gpa: 7.0,
  assignmentCompletion: 75,
  midtermScore: 65,
};

const FIELDS = [
  {
    key: 'attendance',
    label: 'Attendance Rate',
    icon: '📅',
    min: 0, max: 100, step: 1,
    unit: '%',
    desc: 'Percentage of classes attended',
    color: '#6366f1',
  },
  {
    key: 'gpa',
    label: 'CGPA',
    icon: '🎯',
    min: 0, max: 10, step: 0.1,
    unit: '/10',
    desc: 'Cumulative Grade Point Average',
    color: '#8b5cf6',
  },
  {
    key: 'assignmentCompletion',
    label: 'Assignment Completion',
    icon: '📝',
    min: 0, max: 100, step: 1,
    unit: '%',
    desc: 'Percentage of assignments submitted',
    color: '#c084fc',
  },
  {
    key: 'midtermScore',
    label: 'Midterm Score',
    icon: '📊',
    min: 0, max: 100, step: 1,
    unit: '%',
    desc: 'Average midterm examination score',
    color: '#a78bfa',
  },
];

export default function LiveSimulatorModal({ onClose }) {
  const { user } = useAuth();

  const [values, setValues] = useState(INITIAL);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [mode, setMode] = useState('NORMAL');
  const [targetEmail, setTargetEmail] = useState('');
  const [targetDepartment, setTargetDepartment] = useState('');

  const handleChange = (key, val) => {
    setValues(prev => ({ ...prev, [key]: Number(val) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        attendance: values.attendance,
        gpa: values.gpa,
        assignmentCompletion: values.assignmentCompletion,
        midtermScore: values.midtermScore,
        studentName: user?.name,
      };

      if (user?.role === 'STUDENT' && user?._id) {
        payload.studentId = user._id;
      }

      if ((user?.role === 'TEACHER' || user?.role === 'AUTHORITY') && mode === 'ASSIGNED') {
        payload.targetEmail = targetEmail.trim();
        payload.targetDepartment = targetDepartment.trim();
      }

      const { data } = await api.post('/predict', payload);
      setResult(data);

      toast.success(`Prediction complete: ${data.riskLevel} risk (${data.riskScore.toFixed(1)})`);
    } catch (err) {
      const msg = err.response?.data?.message || 'Prediction failed. Ensure the ML service is running.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setValues(INITIAL);
    setResult(null);
    setError(null);
  };

  const RISK_COLORS = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#10b981' };
  const riskColor = result ? RISK_COLORS[result.riskLevel] : '#6366f1';

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content" id="simulator-modal">
        {/* Modal Header */}
        <div style={{
          padding: '24px 28px 20px',
          borderBottom: '1px solid rgba(99, 102, 241, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '42px', height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
            }}>
              <Zap color="white" size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '800', color: '#f1f5f9', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
                AI Risk Simulator
              </h2>
              <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
                Powered by XGBoost Ensemble · 3 Models
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(99, 102, 241, 0.2)',
              borderRadius: '8px', padding: '8px', color: '#64748b', cursor: 'pointer', display: 'flex',
            }}
          >
            <X size={16} />
          </button>
        </div>

        <div style={{ padding: '24px 28px' }}>
          {/* Input Form */}
          <form onSubmit={handleSubmit}>
            {(user?.role === 'TEACHER' || user?.role === 'AUTHORITY') && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px', background: 'rgba(15,23,42,0.5)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(99,102,241,0.1)' }}>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f1f5f9', cursor: 'pointer', fontSize: '14px' }}>
                    <input type="radio" checked={mode === 'NORMAL'} onChange={() => setMode('NORMAL')} />
                    Normal Mode (Simulation)
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f1f5f9', cursor: 'pointer', fontSize: '14px' }}>
                    <input type="radio" checked={mode === 'ASSIGNED'} onChange={() => setMode('ASSIGNED')} />
                    Assign to Student
                  </label>
                </div>
                {mode === 'ASSIGNED' && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Student Email</label>
                      <input required type="email" className="form-input" value={targetEmail} onChange={e => setTargetEmail(e.target.value)} placeholder="student@example.edu" />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Department</label>
                      <input required type="text" className="form-input" value={targetDepartment} onChange={e => setTargetDepartment(e.target.value)} placeholder="Computer Science" />
                    </div>
                  </div>
                )}
              </div>
            )}
            <div style={{ display: 'grid', gap: '20px', marginBottom: '24px' }}>
              {FIELDS.map(({ key, label, icon, min, max, step, unit, desc, color }) => (
                <div key={key} style={{
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(99, 102, 241, 0.12)',
                  borderRadius: '12px',
                  padding: '16px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '18px' }}>{icon}</span>
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '600', color: '#f1f5f9' }}>{label}</div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>{desc}</div>
                      </div>
                    </div>
                    <div style={{
                      background: `rgba(${color === '#6366f1' ? '99,102,241' : color === '#8b5cf6' ? '139,92,246' : color === '#c084fc' ? '192, 132, 252' : '167,139,250'}, 0.15)`,
                      border: `1px solid ${color}40`,
                      borderRadius: '8px',
                      padding: '4px 12px',
                      fontSize: '16px',
                      fontWeight: '700',
                      color: color,
                      fontFamily: 'Space Grotesk, sans-serif',
                      minWidth: '70px',
                      textAlign: 'center',
                    }}>
                      {key === 'gpa' ? values[key].toFixed(1) : Math.round(values[key])}{unit}
                    </div>
                  </div>
                  <input
                    id={`slider-${key}`}
                    type="range"
                    className="slider"
                    min={min}
                    max={max}
                    step={step}
                    value={values[key]}
                    onChange={(e) => handleChange(key, e.target.value)}
                    style={{
                      background: `linear-gradient(to right, ${color} ${((values[key] - min) / (max - min)) * 100}%, rgba(99, 102, 241, 0.2) 0%)`,
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
                    <span style={{ fontSize: '10px', color: '#475569' }}>{min}{unit}</span>
                    <span style={{ fontSize: '10px', color: '#475569' }}>{max}{unit}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Error */}
            {error && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '10px', padding: '12px 16px', marginBottom: '16px',
                display: 'flex', alignItems: 'center', gap: '10px', color: '#f87171', fontSize: '13px',
              }}>
                <AlertTriangle size={16} />
                {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                id="run-prediction-btn"
                type="submit"
                disabled={loading}
                className="btn btn-primary"
                style={{ flex: 1, justifyContent: 'center' }}
              >
                {loading ? (
                  <>
                    <span className="spinner" style={{ width: 16, height: 16, borderWidth: '2px' }} />
                    Running Inference...
                  </>
                ) : (
                  <>
                    <Zap size={16} />
                    Run AI Prediction
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="btn btn-ghost"
                style={{ flexShrink: 0 }}
              >
                Reset
              </button>
            </div>
          </form>

          {/* Results Panel */}
          {result && (
            <div className="animate-fade-in-scale" style={{
              marginTop: '24px',
              background: `linear-gradient(135deg, rgba(${
                result.riskLevel === 'HIGH' ? '239,68,68' :
                result.riskLevel === 'MEDIUM' ? '245,158,11' : '16,185,129'
              }, 0.05), rgba(15,23,42,0.8))`,
              border: `1px solid ${riskColor}30`,
              borderRadius: '16px',
              padding: '24px',
            }}>
              {/* Gauge + Score */}
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
                <RiskGauge score={result.riskScore} riskLevel={result.riskLevel} animated />
              </div>

              {/* Breakdown */}
              {result.breakdown && (
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: '600', marginBottom: '10px' }}>
                    Model Breakdown
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '10px' }}>
                    {[
                      { label: 'Dropout', score: result.breakdown.dropoutScore, icon: TrendingDown, color: '#f43f5e' },
                      { label: 'Wellbeing', score: result.breakdown.wellbeingScore, icon: Activity, color: '#f59e0b' },
                      { label: 'Depression', score: result.breakdown.depressionScore, icon: BarChart2, color: '#8b5cf6' },
                    ].map(({ label, score, icon: Icon, color }) => (
                      <div key={label} style={{
                        background: `rgba(${color === '#f43f5e' ? '244,63,94' : color === '#f59e0b' ? '245,158,11' : '139,92,246'}, 0.08)`,
                        border: `1px solid ${color}25`,
                        borderRadius: '10px',
                        padding: '12px',
                        textAlign: 'center',
                      }}>
                        <Icon size={14} color={color} style={{ marginBottom: 4 }} />
                        <div style={{ fontSize: '18px', fontWeight: '800', color, fontFamily: 'Space Grotesk, sans-serif' }}>
                          {score?.toFixed(1) || '—'}
                        </div>
                        <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>{label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Top Factors */}
              {result.topFactors?.length > 0 && (
                <div>
                  <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: '600', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <AlertTriangle size={11} />
                    Key Risk Factors
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {result.topFactors.map((factor, i) => (
                      <div key={i} style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '10px',
                        padding: '10px 14px',
                        background: 'rgba(15, 23, 42, 0.6)',
                        borderRadius: '8px',
                        border: '1px solid rgba(99, 102, 241, 0.1)',
                      }}>
                        <span style={{
                          width: '20px', height: '20px', borderRadius: '6px',
                          background: 'rgba(99, 102, 241, 0.15)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '10px', fontWeight: '700', color: '#a78bfa',
                          flexShrink: 0,
                        }}>
                          {i + 1}
                        </span>
                        <span style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: '1.4' }}>{factor}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
