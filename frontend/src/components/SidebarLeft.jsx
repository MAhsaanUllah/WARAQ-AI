import React from 'react';
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react';

export default function SidebarLeft({ activeTab, setActiveTab, onNewChat }) {
  return (
    <div className="sidebar" style={{ borderRight: '1px solid var(--md-sys-color-outline-variant)' }}>
      {/* Brand */}
      <div className="flex items-center mt-2" style={{ marginBottom: '2rem', padding: '0 1rem', gap: '0.75rem' }}>
        <div style={{ width: '32px', display: 'flex', justifyContent: 'flex-start' }}>
          <div style={{
            width: '32px', 
            height: '32px', 
            borderRadius: '10px', 
            background: 'linear-gradient(135deg, var(--md-sys-color-surface-container-high), var(--md-sys-color-surface-container-lowest))', 
            border: '1px solid var(--md-sys-color-outline-variant)',
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            boxShadow: '0 4px 12px rgba(0,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.05)',
            flexShrink: 0
          }}>
            <span style={{ 
              fontWeight: '700', 
              fontSize: '1.25rem',
              fontFamily: 'Inter, sans-serif',
              background: 'linear-gradient(135deg, var(--md-sys-color-primary), var(--md-sys-color-tertiary))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '-0.05em'
            }}>
              W
            </span>
          </div>
        </div>
        <h2 style={{ 
          fontSize: '1.2rem', 
          margin: 0, 
          fontWeight: '600', 
          letterSpacing: '-0.02em',
          fontFamily: 'Inter, sans-serif',
          color: 'var(--md-sys-color-on-surface)'
        }}>
          Waraq <span style={{ color: 'var(--md-sys-color-primary)', fontWeight: '700' }}>AI</span>
        </h2>
      </div>

      {/* New Chat Button */}
      <button 
        onClick={onNewChat}
        style={{ 
          width: '100%',
          display: 'flex', 
          alignItems: 'center', 
          gap: '0.75rem',
          padding: '0.75rem 1rem',
          marginBottom: '1.5rem',
          background: 'var(--md-sys-color-primary)',
          color: 'var(--md-sys-color-on-primary)',
          border: 'none',
          borderRadius: 'var(--radius-pill)',
          fontWeight: '600',
          fontSize: '0.95rem',
          cursor: 'pointer',
          boxShadow: 'var(--shadow-sm)',
          transition: 'all 0.2s ease'
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.background = 'var(--md-sys-color-primary-container)';
          e.currentTarget.style.color = 'var(--md-sys-color-on-primary-container)';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.background = 'var(--md-sys-color-primary)';
          e.currentTarget.style.color = 'var(--md-sys-color-on-primary)';
        }}
      >
        <div style={{ width: '32px', display: 'flex', justifyContent: 'flex-start' }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </div>
        New chat
      </button>

      {/* Navigation */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flexGrow: 1 }}>
        <a className={`nav-link ${activeTab === 'query' ? 'active' : ''}`} onClick={() => setActiveTab('query')}>
          <div style={{ width: '32px', display: 'flex', justifyContent: 'flex-start' }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          Explore
        </a>
        
        <a className={`nav-link ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}>
          <div style={{ width: '32px', display: 'flex', justifyContent: 'flex-start' }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="12" y1="18" x2="12" y2="12"></line>
              <line x1="9" y1="15" x2="12" y2="12"></line>
              <line x1="15" y1="15" x2="12" y2="12"></line>
            </svg>
          </div>
          Resources
        </a>

        <a className={`nav-link ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
          <div style={{ width: '32px', display: 'flex', justifyContent: 'flex-start' }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </div>
          Settings
        </a>
      </div>

      {/* Auth */}
      <div style={{ marginTop: 'auto', padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <SignedIn>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%', padding: '0.5rem', background: 'var(--md-sys-color-surface-container-high)', borderRadius: 'var(--radius-md)' }}>
            <UserButton afterSignOutUrl="/" appearance={{ elements: { userButtonAvatarBox: { width: '32px', height: '32px' } } }} />
            <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: '500' }}>My Account</span>
          </div>
        </SignedIn>
        <SignedOut>
          <SignInButton mode="modal">
            <button className="btn btn-primary" style={{ width: '100%', display: 'flex', justifyContent: 'center', padding: '0.75rem' }}>
              Sign In
            </button>
          </SignInButton>
        </SignedOut>
      </div>
    </div>
  );
}
