import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { streamQuery, uploadDocuments } from '../api';
import SourceCard from './SourceCard';
import { useAuth } from '@clerk/clerk-react';

export default function QueryPage({ sessionId, initialHistory, onUpdateSession, settings }) {
  const { getToken } = useAuth();
  const [question, setQuestion] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  
  const [showResourcesModal, setShowResourcesModal] = useState(false);
  const [resources, setResources] = useState([]);
  const [isLoadingResources, setIsLoadingResources] = useState(false);
  const [selectedResourceIds, setSelectedResourceIds] = useState([]);
  
  const [history, setHistory] = useState(initialHistory || [
    { role: 'ai', text: 'Hello! I am Waraq AI. I can answer questions based on the documents you upload.', sources: [] }
  ]);
  
  const abortStreamRef = useRef(null);
  const endOfChatRef = useRef(null);
  const fileInputRef = useRef(null);

  // Sync with App on history change
  useEffect(() => {
    if (onUpdateSession) {
      onUpdateSession(sessionId, history);
    }
  }, [history, sessionId]);

  useEffect(() => {
    if (endOfChatRef.current) {
      endOfChatRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [history, statusMsg, isUploading]);

  useEffect(() => {
    return () => {
      if (abortStreamRef.current) abortStreamRef.current();
    };
  }, []);



  const handleFileUpload = async (e) => {
    const files = e.target.files && Array.from(e.target.files);
    if (!files || files.length === 0) return;
    
    setHistory(prev => [
      ...prev,
      { role: 'user', text: `📎 Uploading ${files.length} file${files.length !== 1 ? 's' : ''}...` }
    ]);
    setIsUploading(true);
    
    try {
      const token = await getToken();
      const result = await uploadDocuments(files, token);
      setHistory(prev => [
        ...prev,
        { role: 'ai', text: `✅ Successfully indexed **${result.results.length}** file(s)! (${result.total_pages} pages, ${result.total_chunks} chunks). You can now ask me questions about them.` }
      ]);
    } catch (err) {
      setHistory(prev => [
        ...prev,
        { role: 'ai', text: `❌ Failed to upload files: ${err.message}` }
      ]);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const fetchResources = async () => {
    setIsLoadingResources(true);
    try {
      const token = await getToken();
      const baseUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${baseUrl}/api/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setResources(data);
      } else {
        throw new Error('Failed to fetch documents from backend');
      }
    } catch (e) {
      console.error(e);
      setResources([]);
    } finally {
      setIsLoadingResources(false);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!question.trim() || isStreaming || isUploading) return;
    
    const userQ = question;
    setQuestion('');
    
    setHistory(prev => [
      ...prev, 
      { role: 'user', text: userQ },
      { role: 'ai', text: '', sources: [] }
    ]);
    
    setStatusMsg('Initializing query...');
    setIsStreaming(true);

    if (abortStreamRef.current) abortStreamRef.current();

    const token = await getToken();
    abortStreamRef.current = streamQuery(
      userQ,
      settings,
      webSearchEnabled,
      selectedResourceIds,
      (type, data) => {
        if (type === 'status') {
          setStatusMsg(data.message);
        } else if (type === 'answer_delta') {
          setHistory(prev => {
            const newHistory = [...prev];
            const lastIdx = newHistory.length - 1;
            newHistory[lastIdx].text += data.delta;
            return newHistory;
          });
        }
      },
      (errMsg) => {
        setHistory(prev => {
          const newHistory = [...prev];
          const lastIdx = newHistory.length - 1;
          newHistory[lastIdx].text += `\n\n**Error:** ${errMsg}`;
          return newHistory;
        });
        setIsStreaming(false);
        setStatusMsg('');
        if (webSearchEnabled) {
          setWebSearchEnabled(false);
        }
      },
      (doneData) => {
        setHistory(prev => {
          const newHistory = [...prev];
          const lastIdx = newHistory.length - 1;
          newHistory[lastIdx].sources = doneData.sources || [];
          return newHistory;
        });
        setIsStreaming(false);
        setStatusMsg('');
      },
      token
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '1.5rem', paddingRight: '2rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', padding: '0.75rem 1.5rem', background: 'var(--md-sys-color-surface-container-high)', borderRadius: 'var(--radius-pill)', boxShadow: 'var(--shadow-sm)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.15rem' }}>Waraq AI Chat</h2>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', borderLeft: '1px solid var(--md-sys-color-outline-variant)', paddingLeft: '1rem' }}>
            Intelligent Document Retrieval with Pinpoint Citations
          </span>
        </div>
      </div>

      {/* Chat Area */}
      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {history.map((msg, idx) => (
          <div key={idx} style={{ 
            display: 'flex', 
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            gap: '1rem',
            alignItems: 'flex-end'
          }}>
            {msg.role === 'ai' && (
              <div style={{ 
                width: '36px', height: '36px', borderRadius: '50%', 
                background: 'linear-gradient(135deg, var(--md-sys-color-surface-container-high), var(--md-sys-color-surface-container-lowest))',
                border: '1px solid var(--md-sys-color-outline-variant)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', 
                flexShrink: 0, boxShadow: '0 4px 12px rgba(0,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.05)' 
              }}>
                <span style={{ 
                  fontWeight: '700', fontSize: '1.25rem', fontFamily: 'Inter, sans-serif',
                  background: 'linear-gradient(135deg, var(--md-sys-color-primary), var(--md-sys-color-tertiary))',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', letterSpacing: '-0.05em'
                }}>
                  W
                </span>
              </div>
            )}
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: '80%', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div className="surface-card" style={{ 
                padding: '1rem 1.5rem', 
                background: msg.role === 'user' ? 'var(--md-sys-color-primary-container)' : 'var(--md-sys-color-surface-container-low)',
                borderRadius: msg.role === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                boxShadow: msg.role === 'user' ? 'none' : 'var(--shadow-sm)'
              }}>
                {msg.text ? (
                   <div className="markdown-body" style={{ color: msg.role === 'user' ? 'var(--md-sys-color-on-primary-container)' : 'var(--md-sys-color-on-surface)', fontSize: '0.95rem' }}>
                     <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                   </div>
                ) : isStreaming && idx === history.length - 1 ? (
                   <div className="text-muted" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                     <span className="animate-pulse">●</span> {statusMsg || 'Thinking...'}
                   </div>
                ) : null}
              </div>

              {msg.sources && msg.sources.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.25rem', width: '100%' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>Sources:</span>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {msg.sources.map((src, sIdx) => (
                      <SourceCard key={sIdx} source={src} index={sIdx} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
               <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--md-sys-color-secondary)', color: 'var(--md-sys-color-on-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem', flexShrink: 0, boxShadow: 'var(--shadow-sm)' }}>
                 👤
               </div>
            )}
          </div>
        ))}
        {isUploading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', gap: '1rem', alignItems: 'flex-end' }}>
             <div style={{ 
                width: '36px', height: '36px', borderRadius: '50%', 
                background: 'linear-gradient(135deg, var(--md-sys-color-surface-container-high), var(--md-sys-color-surface-container-lowest))',
                border: '1px solid var(--md-sys-color-outline-variant)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', 
                flexShrink: 0, boxShadow: '0 4px 12px rgba(0,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.05)' 
              }}>
                <span style={{ 
                  fontWeight: '700', fontSize: '1.25rem', fontFamily: 'Inter, sans-serif',
                  background: 'linear-gradient(135deg, var(--md-sys-color-primary), var(--md-sys-color-tertiary))',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', letterSpacing: '-0.05em'
                }}>
                  W
                </span>
              </div>
              <div className="surface-card text-muted" style={{ padding: '1rem 1.5rem', borderRadius: '20px 20px 20px 4px', display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--md-sys-color-surface-container-low)' }}>
                <span className="animate-pulse">●</span> Indexing document...
              </div>
          </div>
        )}
        <div ref={endOfChatRef} style={{ height: '10px' }} />
      </div>

      {/* Input Area */}
      <div style={{ marginTop: '0.5rem' }}>
        <div className="surface-card" style={{ padding: '1rem', borderRadius: 'var(--radius-lg)' }}>
          {/* Pills */}
          <div className="flex gap-2 mb-4" style={{ paddingLeft: '0.5rem' }}>
            <span 
              className="btn" 
              onClick={() => {
                setShowResourcesModal(true);
                fetchResources();
              }}
              style={{ background: 'var(--md-sys-color-tertiary-container)', color: 'var(--md-sys-color-on-tertiary-container)', border: '1px solid var(--md-sys-color-tertiary)', fontSize: '0.8rem', padding: '0.25rem 0.75rem', cursor: 'pointer' }}>
              📂 Add from resources
            </span>
            <span 
              className="btn" 
              onClick={() => setWebSearchEnabled(!webSearchEnabled)}
              style={{ 
                background: webSearchEnabled ? 'var(--md-sys-color-primary)' : 'var(--md-sys-color-secondary-container)', 
                color: webSearchEnabled ? 'var(--md-sys-color-on-primary)' : 'var(--md-sys-color-on-secondary-container)', 
                border: `1px solid ${webSearchEnabled ? 'var(--md-sys-color-primary)' : 'var(--md-sys-color-secondary)'}`, 
                fontSize: '0.8rem', 
                padding: '0.25rem 0.75rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}>
              🌐 Web search
            </span>
            <span 
              className="btn" 
              onClick={() => setQuestion(prev => prev ? prev + ' Based on my documents, write code to: ' : 'Based on my documents, write code to: ')}
              style={{ background: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)', border: '1px solid var(--md-sys-color-outline-variant)', fontSize: '0.8rem', padding: '0.25rem 0.75rem', cursor: 'pointer' }}>
              {'</>'} Code
            </span>

          </div>
          
          <form onSubmit={handleQuery} className="flex gap-2 items-center" style={{ background: 'var(--md-sys-color-surface-container-highest)', borderRadius: 'var(--radius-pill)', padding: '0.5rem 0.5rem 0.5rem 1rem' }}>
            <input 
              type="file" 
              multiple
              accept="application/pdf"
              ref={fileInputRef}
              onChange={handleFileUpload}
              style={{ display: 'none' }} 
            />
            <span 
              onClick={() => fileInputRef.current?.click()}
              style={{ color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem', transition: 'color 0.2s' }}
              onMouseOver={(e) => e.target.style.color = 'var(--md-sys-color-primary)'}
              onMouseOut={(e) => e.target.style.color = 'var(--text-muted)'}
              title="Upload PDF Document"
            >
              📎
            </span>

            {selectedResourceIds.length > 0 && (
              <span style={{ 
                background: 'var(--md-sys-color-tertiary-container)', 
                color: 'var(--md-sys-color-on-tertiary-container)', 
                fontSize: '0.75rem', 
                fontWeight: '600', 
                padding: '0.2rem 0.5rem', 
                borderRadius: 'var(--radius-sm)',
                whiteSpace: 'nowrap'
              }}>
                {selectedResourceIds.length} docs
              </span>
            )}

            <input 
              type="text" 
              value={question}
              onChange={e => setQuestion(e.target.value)}
              disabled={isStreaming || isUploading}
              placeholder="Ask me something..."
              style={{ flexGrow: 1, background: 'transparent', border: 'none', outline: 'none', padding: '0.5rem', fontSize: '1rem', color: 'var(--text-primary)' }}
            />
            <button type="submit" disabled={!question.trim() || isStreaming || isUploading} className="btn-primary" style={{ width: '40px', height: '40px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}>
              <span style={{ transform: 'translateX(2px)' }}>➤</span>
            </button>
          </form>
        </div>
      </div>

      {/* Select Resources Modal */}
      {showResourcesModal && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="surface-card" style={{ width: '90%', maxWidth: '600px', padding: '2rem', display: 'flex', flexDirection: 'column', maxHeight: '80vh' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.3rem' }}>Select Resources</h2>
              <button onClick={() => setShowResourcesModal(false)} className="btn-icon" style={{ background: 'transparent', border: 'none' }}>✕</button>
            </div>
            
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
              Select specific documents to restrict the AI's search context.
            </p>

            <div style={{ overflowY: 'auto', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem', paddingRight: '0.5rem' }}>
              {isLoadingResources ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>Loading resources...</div>
              ) : resources.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No resources found. Upload some first!</div>
              ) : (
                resources.map(res => (
                  <div key={res.document_id} 
                    onClick={() => {
                      setSelectedResourceIds(prev => 
                        prev.includes(res.document_id) 
                          ? prev.filter(id => id !== res.document_id)
                          : [...prev, res.document_id]
                      )
                    }}
                    style={{ 
                      padding: '1rem', 
                      borderRadius: 'var(--radius-sm)', 
                      border: `1px solid ${selectedResourceIds.includes(res.document_id) ? 'var(--md-sys-color-primary)' : 'var(--md-sys-color-outline-variant)'}`,
                      background: selectedResourceIds.includes(res.document_id) ? 'var(--md-sys-color-primary-container)' : 'var(--md-sys-color-surface-container-high)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      transition: 'all 0.2s'
                  }}>
                    <div style={{ 
                      width: '24px', height: '24px', borderRadius: '4px', border: '2px solid var(--md-sys-color-primary)', 
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: selectedResourceIds.includes(res.document_id) ? 'var(--md-sys-color-primary)' : 'transparent'
                    }}>
                      {selectedResourceIds.includes(res.document_id) && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--md-sys-color-on-primary)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>}
                    </div>
                    <div>
                      <div style={{ fontWeight: '600', color: selectedResourceIds.includes(res.document_id) ? 'var(--md-sys-color-on-primary-container)' : 'var(--text-primary)' }}>{res.filename}</div>
                      <div style={{ fontSize: '0.8rem', color: selectedResourceIds.includes(res.document_id) ? 'var(--md-sys-color-on-primary-container)' : 'var(--text-secondary)', opacity: 0.8 }}>{res.pages} pages • {res.chunks} chunks</div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button className="btn" onClick={() => setShowResourcesModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={() => setShowResourcesModal(false)}>
                Apply Selection ({selectedResourceIds.length})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
