import { useNavigate, useLocation, Link } from 'react-router-dom';
import { LogOut, Zap, Activity, Users, Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import NotificationPanel from './NotificationPanel';

const ROLE_ROUTES = {
  STUDENT: '/student',
  TEACHER: '/teacher',
  AUTHORITY: '/authority',
};

export default function Header({ onOpenSimulator }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinks = [
    { to: '/student', label: 'Student Portal', icon: Activity, role: 'STUDENT' },
    { to: '/teacher', label: 'Teacher Dashboard', icon: Users, role: 'TEACHER' },
    { to: '/authority', label: 'Authority View', icon: Shield, role: 'AUTHORITY' },
  ];

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      background: 'rgba(11, 15, 25, 0.92)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(99, 102, 241, 0.15)',
      padding: '0 24px',
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '64px',
        gap: '16px',
      }}>
        {/* Logo */}
        <Link to={ROLE_ROUTES[user?.role] || '/login'} style={{ textDecoration: 'none', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
            }}>
              <Zap size={18} color="white" />
            </div>
            <div>
              <div style={{
                fontSize: '18px',
                fontWeight: '800',
                fontFamily: 'Space Grotesk, sans-serif',
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #c084fc)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                lineHeight: 1,
              }}>
                DISHA
              </div>
              <div style={{ fontSize: '9px', color: '#64748b', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                AI Risk Platform
              </div>
            </div>
          </div>
        </Link>

        {/* Nav Links — only show the current role's link + others for context */}
        <nav style={{ display: 'flex', gap: '4px', flex: 1, justifyContent: 'center' }}>
          {navLinks.filter(({ role }) => user?.role === role).map(({ to, label, icon: Icon, role }) => {
            const isActive = location.pathname === to;
            const isCurrent = user?.role === role;
            return (
              <Link
                key={to}
                to={to}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: isActive ? '600' : '400',
                  color: isActive ? '#a78bfa' : '#94a3b8',
                  background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
                  textDecoration: 'none',
                  transition: 'all 0.2s ease',
                  opacity: isCurrent || isActive ? 1 : 0.7,
                }}
              >
                <Icon size={14} />
                <span style={{ display: window.innerWidth < 768 ? 'none' : 'inline' }}>
                  {label}
                </span>
              </Link>
            );
          })}
        </nav>

        {/* Right Side */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>

          {/* Live Simulator Button */}
          {onOpenSimulator && (
            <button
              id="open-simulator-btn"
              onClick={onOpenSimulator}
              className="btn btn-primary btn-sm"
              style={{ gap: '6px' }}
            >
              <Zap size={14} />
              AI Simulator
            </button>
          )}

          {/* Notification Bell */}
          {user?.role !== 'STUDENT' && <NotificationPanel />}

          {/* User Avatar + Logout */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '34px',
              height: '34px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
              fontWeight: '700',
              color: 'white',
              flexShrink: 0,
            }}>
              {user?.name?.charAt(0) || '?'}
            </div>
            <div style={{ display: window.innerWidth < 1024 ? 'none' : 'block' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#f1f5f9', lineHeight: 1 }}>
                {user?.name?.split(' ')[0]}
              </div>
              <div style={{
                fontSize: '10px',
                color: '#64748b',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}>
                {user?.role}
              </div>
            </div>

            <button
              id="logout-btn"
              onClick={handleLogout}
              title="Logout"
              style={{
                background: 'transparent',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                borderRadius: '8px',
                padding: '6px',
                color: '#ef4444',
                cursor: 'pointer',
                display: 'flex',
                transition: 'all 0.2s',
              }}
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
