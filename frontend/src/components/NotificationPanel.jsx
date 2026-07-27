import { useState, useRef, useEffect } from 'react';
import { Bell, X, Check, CheckCheck, Trash2, AlertTriangle, Info } from 'lucide-react';
import { useNotifications } from '../contexts/NotificationContext';

export default function NotificationPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const panelRef = useRef(null);
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications();

  // Close on outside click
  useEffect(() => {
    function handleClick(e) {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen]);

  const getRiskColor = (level) => {
    if (level === 'HIGH') return '#ef4444';
    if (level === 'MEDIUM') return '#f59e0b';
    return '#10b981';
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return 'just now';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    const hrs = Math.floor(mins / 60);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <div ref={panelRef} style={{ position: 'relative' }}>
      {/* Bell Button */}
      <button
        id="notification-bell-btn"
        onClick={() => setIsOpen(prev => !prev)}
        style={{
          position: 'relative',
          background: isOpen
            ? 'rgba(99, 102, 241, 0.2)'
            : 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: '10px',
          padding: '8px',
          cursor: 'pointer',
          color: '#a78bfa',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s ease',
        }}
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: '-5px',
            right: '-5px',
            background: 'linear-gradient(135deg, #ef4444, #dc2626)',
            color: 'white',
            fontSize: '10px',
            fontWeight: '700',
            borderRadius: '10px',
            padding: '1px 5px',
            minWidth: '18px',
            textAlign: 'center',
            border: '1.5px solid #0B0F19',
          }}>
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="animate-fade-in" style={{
          position: 'absolute',
          top: 'calc(100% + 10px)',
          right: 0,
          width: '380px',
          background: 'rgba(15, 23, 42, 0.97)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: '16px',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 24px 60px rgba(0,0,0,0.7), 0 0 0 1px rgba(99, 102, 241, 0.1)',
          zIndex: 200,
          overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            padding: '16px 20px',
            borderBottom: '1px solid rgba(99, 102, 241, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#f1f5f9', margin: 0 }}>
                Alerts
              </h3>
              <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
                {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up'}
              </p>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  title="Mark all as read"
                  style={{
                    background: 'rgba(99, 102, 241, 0.1)',
                    border: '1px solid rgba(99, 102, 241, 0.2)',
                    borderRadius: '8px',
                    padding: '5px',
                    color: '#a78bfa',
                    cursor: 'pointer',
                    display: 'flex',
                  }}
                >
                  <CheckCheck size={14} />
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer',
                  display: 'flex',
                  padding: '5px',
                }}
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Notifications List */}
          <div style={{ maxHeight: '380px', overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <div style={{ padding: '40px 20px', textAlign: 'center' }}>
                <div style={{ fontSize: '36px', marginBottom: '10px', opacity: 0.4 }}>🔔</div>
                <p style={{ color: '#64748b', fontSize: '14px' }}>No notifications yet</p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif._id || notif.tempId}
                  style={{
                    padding: '14px 20px',
                    borderBottom: '1px solid rgba(99, 102, 241, 0.06)',
                    background: notif.isRead ? 'transparent' : 'rgba(99, 102, 241, 0.04)',
                    display: 'flex',
                    gap: '12px',
                    alignItems: 'flex-start',
                    cursor: 'pointer',
                    transition: 'background 0.15s ease',
                  }}
                  onClick={() => !notif.isRead && markAsRead(notif._id)}
                >
                  {/* Icon */}
                  <div style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '10px',
                    background: `rgba(${
                      notif.riskLevel === 'HIGH' ? '239,68,68' :
                      notif.riskLevel === 'MEDIUM' ? '245,158,11' : '16,185,129'
                    }, 0.12)`,
                    border: `1px solid rgba(${
                      notif.riskLevel === 'HIGH' ? '239,68,68' :
                      notif.riskLevel === 'MEDIUM' ? '245,158,11' : '16,185,129'
                    }, 0.3)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <AlertTriangle
                      size={14}
                      color={getRiskColor(notif.riskLevel)}
                    />
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: '13px',
                      fontWeight: notif.isRead ? '400' : '600',
                      color: '#f1f5f9',
                      lineHeight: '1.4',
                      marginBottom: '4px',
                    }}>
                      {notif.message}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        fontSize: '10px',
                        fontWeight: '700',
                        padding: '2px 6px',
                        borderRadius: '6px',
                        color: getRiskColor(notif.riskLevel),
                        background: `rgba(${
                          notif.riskLevel === 'HIGH' ? '239,68,68' :
                          notif.riskLevel === 'MEDIUM' ? '245,158,11' : '16,185,129'
                        }, 0.1)`,
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                      }}>
                        {notif.riskLevel}
                      </span>
                      <span style={{ fontSize: '11px', color: '#64748b' }}>
                        {formatTime(notif.createdAt)}
                      </span>
                      {!notif.isRead && (
                        <span style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          background: '#6366f1',
                          display: 'inline-block',
                        }} />
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
