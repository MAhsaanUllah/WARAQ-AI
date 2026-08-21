import React, { useState } from 'react';
import { uploadDocuments } from '../api';
import { useAuth } from '@clerk/clerk-react';

export default function UploadPage({ onUploadSuccess }) {
  const { getToken } = useAuth();
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(prev => [...prev, ...Array.from(e.target.files)]);
      setError('');
      setProgress(null);
    }
    // reset input so the same files can be selected again if needed
    e.target.value = null;
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setIsUploading(true);
    setError('');
    
    try {
      const token = await getToken();
      const result = await uploadDocuments(files, token);
      setProgress(result);
      setTimeout(() => {
        onUploadSuccess(result);
      }, 1500);
    } catch (err) {
      setError(err.message || 'An error occurred during upload.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '1.5rem', alignItems: 'center', justifyContent: 'center' }}>
      
      <div className="surface-card" style={{ padding: '3rem', width: '100%', maxWidth: '600px', textAlign: 'center' }}>
        <h2 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>Upload Resources</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
          Select PDFs to add to your Waraq AI resource library.
        </p>
        
        <div style={{ marginBottom: '2rem' }}>
          <input 
            type="file" 
            multiple
            accept="application/pdf" 
            onChange={handleFileChange}
            id="file-upload"
            style={{ display: 'none' }}
          />
          <label 
            htmlFor="file-upload" 
            className="btn" 
            style={{ 
              display: 'block', 
              width: '100%', 
              padding: '2rem 1rem', 
              border: `2px dashed var(--md-sys-color-outline-variant)`,
              background: 'var(--md-sys-color-surface-container-high)',
              borderRadius: 'var(--radius-lg)',
              marginBottom: '1rem'
            }}
          >
            <span style={{ color: 'var(--text-muted)' }}>Click to browse or drag and drop PDFs</span>
          </label>
          
          {files.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left' }}>
              {files.map((f, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--md-sys-color-surface-container)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--md-sys-color-outline-variant)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', overflow: 'hidden' }}>
                    <span style={{ fontSize: '1.25rem' }}>📄</span>
                    <span style={{ color: 'var(--md-sys-color-on-surface)', fontWeight: '500', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.name}</span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({(f.size / 1024 / 1024).toFixed(2)} MB)</span>
                  </div>
                  <button onClick={() => removeFile(i)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem', padding: '0.25rem' }}>✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div style={{ color: 'var(--md-sys-color-on-error-container)', marginBottom: '1.5rem', padding: '1rem', background: 'var(--md-sys-color-error-container)', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}

        {progress && (
          <div style={{ color: 'var(--md-sys-color-on-primary-container)', marginBottom: '1.5rem', padding: '1rem', background: 'var(--md-sys-color-primary-container)', borderRadius: 'var(--radius-sm)', fontSize: '0.95rem' }}>
            Successfully indexed <strong>{progress.total_pages}</strong> pages and <strong>{progress.total_chunks}</strong> chunks across {progress.results.length} files!
          </div>
        )}

        <button 
          className="btn btn-primary" 
          onClick={handleUpload} 
          disabled={files.length === 0 || isUploading}
          style={{ width: '100%', padding: '1rem', borderRadius: 'var(--radius-md)' }}
        >
          {isUploading ? (
            <span className="animate-pulse">Processing & Indexing...</span>
          ) : (
            `Upload & Index (${files.length} file${files.length !== 1 ? 's' : ''})`
          )}
        </button>
      </div>
    </div>
  );
}
