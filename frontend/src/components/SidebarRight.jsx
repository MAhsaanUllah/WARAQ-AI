import React from 'react';

export default function SidebarRight({ sessions, activeSessionId, onSelectSession, onDeleteHistory }) {
  const sortedSessions = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <div className="sidebar" style={{ borderLeft: '1px solid var(--md-sys-color-outline-variant)' }}>
      <h3 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', fontWeight: '500' }}>History</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flexGrow: 1, overflowY: 'auto', paddingRight: '0.5rem' }}>
        {sortedSessions.length === 0 ? (
          <p className="text-muted" style={{ fontSize: '0.9rem', textAlign: 'center', marginTop: '2rem' }}>No history yet.</p>
        ) : (
          sortedSessions.map(session => (
            <div 
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              style={{ 
                cursor: 'pointer', 
                opacity: session.id === activeSessionId ? 1 : 0.6,
                background: session.id === activeSessionId ? 'var(--md-sys-color-secondary-container)' : 'transparent',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => { if (session.id !== activeSessionId) e.currentTarget.style.opacity = '1'; }}
              onMouseOut={(e) => { if (session.id !== activeSessionId) e.currentTarget.style.opacity = '0.6'; }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                <span className="text-muted">📁</span>
                <h4 style={{ fontSize: '0.9rem', margin: 0, fontWeight: '500', color: session.id === activeSessionId ? 'var(--md-sys-color-on-secondary-container)' : 'var(--text-secondary)' }}>
                  {session.title.length > 25 ? session.title.substring(0, 25) + '...' : session.title}
                </h4>
              </div>
            </div>
          ))
        )}
      </div>

      <button onClick={onDeleteHistory} className="btn" style={{ width: '100%', padding: '0.85rem', color: 'var(--md-sys-color-error)', background: 'var(--md-sys-color-surface-container-high)', fontWeight: '500', marginTop: 'auto' }}>
        🗑 Delete history
      </button>
    </div>
  );
}
