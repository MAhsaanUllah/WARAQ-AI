import React, { useState } from 'react';

export default function SourceCard({ source, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="surface-card" style={{ marginBottom: '0.5rem', overflow: 'hidden', border: '1px solid var(--md-sys-color-outline-variant)' }}>
      <div 
        onClick={() => setExpanded(!expanded)}
        style={{ 
          padding: '0.75rem 1rem', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          cursor: 'pointer',
          background: expanded ? 'var(--md-sys-color-surface-container-highest)' : 'transparent',
          transition: 'background 0.2s'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ 
            background: 'var(--md-sys-color-primary)', 
            color: 'var(--md-sys-color-on-primary)', 
            borderRadius: 'var(--radius-pill)', 
            width: '24px', 
            height: '24px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            fontSize: '0.75rem',
            fontWeight: '600'
          }}>
            {index + 1}
          </span>
          <span style={{ fontSize: '0.9rem', fontWeight: '500', color: 'var(--text-primary)' }}>
            Page {source.page}
          </span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {(source.score * 100).toFixed(0)}%
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
            {expanded ? '▲' : '▼'}
          </span>
        </div>
      </div>
      
      {expanded && (
        <div className="animate-fade-in" style={{ padding: '1rem', borderTop: '1px solid var(--md-sys-color-outline-variant)', background: 'var(--md-sys-color-surface-container-highest)' }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontStyle: 'italic', margin: 0, whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
            "{source.snippet}"
          </p>
          {source.bbox && (
            <div style={{ marginTop: '0.75rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              bbox: [{source.bbox.x0.toFixed(1)}, {source.bbox.y0.toFixed(1)}, {source.bbox.x1.toFixed(1)}, {source.bbox.y1.toFixed(1)}]
            </div>
          )}
        </div>
      )}
    </div>
  );
}
