import React, { useState, useEffect } from 'react';
import { getLLMSettings, setLLMSettings, setSearchSettings } from '../api';

export default function SettingsPage({ settings, setSettings }) {
  const [showKey, setShowKey] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const [showSearchKey, setShowSearchKey] = useState(false);
  const [searchStatusMessage, setSearchStatusMessage] = useState('');
  const [isSavingSearch, setIsSavingSearch] = useState(false);

  useEffect(() => {
    getLLMSettings()
      .then(data => {
        setSettings(prev => ({ 
          ...prev, 
          provider: data.provider,
          searchProvider: data.search_provider || 'tavily'
        }));
        setStatusMessage(data.has_api_key 
          ? `Provider: ${data.provider} — key saved in backend memory` 
          : `Provider: ${data.provider} — no key set`);
        
        setSearchStatusMessage(data.has_search_key
          ? `Web search: ${data.search_provider} — key saved in backend memory`
          : `Web search: ${data.search_provider || 'tavily'} — no key set`);
      })
      .catch(err => {
        console.error(err);
        setStatusMessage('Warning: Could not connect to backend settings API');
        setSearchStatusMessage('Warning: Could not connect to backend settings API');
      });
  }, [setSettings]);

  const handleSaveConfig = async () => {
    setIsSaving(true);
    setStatusMessage('');
    try {
      const result = await setLLMSettings({
        provider: settings.provider || 'deepseek',
        apiKey: settings.apiKey || ''
      });
      setStatusMessage(result.has_api_key 
        ? `Success! Provider: ${result.provider} — key saved in backend memory` 
        : `Success! Provider: ${result.provider} — no key set`);
    } catch (err) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSearchConfig = async () => {
    setIsSavingSearch(true);
    setSearchStatusMessage('');
    try {
      const result = await setSearchSettings({
        provider: settings.searchProvider || 'tavily',
        apiKey: settings.searchApiKey || ''
      });
      setSearchStatusMessage(result.has_search_key 
        ? `Success! Web search: ${result.search_provider} — key saved in backend memory` 
        : `Success! Web search: ${result.search_provider} — no key set`);
    } catch (err) {
      setSearchStatusMessage(`Error: ${err.message}`);
    } finally {
      setIsSavingSearch(false);
    }
  };
  
  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setSettings(prev => ({ 
      ...prev, 
      [name]: type === 'range' || type === 'number' ? parseInt(value, 10) : value 
    }));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '1.5rem 2rem', overflowY: 'auto' }}>
      
      {/* Page Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontWeight: '700', letterSpacing: '-0.02em' }}>Settings</h2>
        <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '0.9rem' }}>Manage your Waraq AI configuration and preferences.</p>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', 
        gap: '1.5rem', 
        width: '100%',
        maxWidth: '1000px'
      }}>
        
        {/* Retrieval Settings Section */}
        <section>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: 'var(--md-sys-color-primary-container)', color: 'var(--md-sys-color-on-primary-container)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'var(--shadow-sm)' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </div>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>Retrieval Settings</h3>
          </div>
          
          <div className="surface-card" style={{ padding: '1.25rem', border: '1px solid var(--md-sys-color-outline-variant)' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <label htmlFor="topKCandidates" style={{ display: 'block', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.15rem', fontSize: '0.95rem' }}>
                    Top K Candidates (Hybrid)
                  </label>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Initial document chunks retrieved using dense & sparse search.
                  </p>
                </div>
                <div style={{ background: 'var(--md-sys-color-primary-container)', color: 'var(--md-sys-color-on-primary-container)', padding: '0.2rem 0.75rem', borderRadius: 'var(--radius-pill)', fontWeight: '700', fontSize: '0.85rem', boxShadow: 'var(--shadow-sm)' }}>
                  {settings.topKCandidates || 25}
                </div>
              </div>
              <input 
                type="range" 
                id="topKCandidates"
                name="topKCandidates"
                min="10" max="100" step="5"
                value={settings.topKCandidates || 25} 
                onChange={handleChange}
                style={{ width: '100%', accentColor: 'var(--md-sys-color-primary)', cursor: 'pointer', height: '4px' }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <label htmlFor="topKFinal" style={{ display: 'block', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.15rem', fontSize: '0.95rem' }}>
                    Top K Final (Cross-Encoder)
                  </label>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Highly accurate chunks sent to the LLM for final generation.
                  </p>
                </div>
                <div style={{ background: 'var(--md-sys-color-primary-container)', color: 'var(--md-sys-color-on-primary-container)', padding: '0.2rem 0.75rem', borderRadius: 'var(--radius-pill)', fontWeight: '700', fontSize: '0.85rem', boxShadow: 'var(--shadow-sm)' }}>
                  {settings.topKFinal || 5}
                </div>
              </div>
              <input 
                type="range" 
                id="topKFinal"
                name="topKFinal"
                min="1" max="20" step="1"
                value={settings.topKFinal || 5} 
                onChange={handleChange}
                style={{ width: '100%', accentColor: 'var(--md-sys-color-primary)', cursor: 'pointer', height: '4px' }}
              />
            </div>

            <div style={{ padding: '0.75rem 1rem', background: 'rgba(156, 214, 125, 0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(156, 214, 125, 0.2)', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <svg style={{ color: 'var(--md-sys-color-primary)', flexShrink: 0, marginTop: '2px' }} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--md-sys-color-on-surface-variant)', lineHeight: '1.5' }}>
                Higher values improve context but increase latency. Modifies <code style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 4px', borderRadius: '4px' }}>top_k</code> query limits.
              </p>
            </div>
          </div>
        </section>

        {/* System Configuration Section */}
        <section>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: 'var(--md-sys-color-surface-container-high)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'var(--shadow-sm)' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
            </div>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>System Configuration</h3>
          </div>

          <div className="surface-card" style={{ padding: '1.25rem', border: '1px solid var(--md-sys-color-outline-variant)' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '0.95rem' }}>LLM Provider & Key</h4>
            <p style={{ margin: '0 0 1.25rem 0', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Select your preferred AI provider and enter your API key to override the server defaults. Keys are stored locally.
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label htmlFor="provider" style={{ display: 'block', fontWeight: '500', color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                  AI Provider
                </label>
                <select 
                  id="provider" 
                  name="provider" 
                  value={settings.provider || 'deepseek'} 
                  onChange={handleChange}
                  style={{ 
                    width: '100%', 
                    padding: '0.6rem 0.75rem', 
                    background: 'var(--md-sys-color-surface-container-high)', 
                    border: '1px solid var(--md-sys-color-outline-variant)', 
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    fontSize: '0.9rem',
                    outline: 'none'
                  }}
                >
                  <option value="deepseek">DeepSeek</option>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="anthropic">Anthropic Claude</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="groq">Groq</option>
                </select>
              </div>

              <div>
                <label htmlFor="apiKey" style={{ display: 'block', fontWeight: '500', color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                  API Key
                </label>
                <div style={{ position: 'relative' }}>
                  <input 
                    type={showKey ? 'text' : 'password'} 
                    id="apiKey" 
                    name="apiKey" 
                    value={settings.apiKey || ''} 
                    onChange={handleChange}
                    placeholder="Enter your API key..."
                    style={{ 
                      width: '100%', 
                      padding: '0.6rem 2.5rem 0.6rem 0.75rem', 
                      background: 'var(--md-sys-color-surface-container-high)', 
                      border: '1px solid var(--md-sys-color-outline-variant)', 
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--text-primary)',
                      fontSize: '0.9rem',
                      outline: 'none'
                    }}
                  />
                  <div 
                    onClick={() => setShowKey(!showKey)}
                    style={{ 
                      position: 'absolute', 
                      right: '0.75rem', 
                      top: '50%', 
                      transform: 'translateY(-50%)',
                      cursor: 'pointer',
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    title={showKey ? "Hide API Key" : "Show API Key"}
                  >
                    {showKey ? (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    )}
                  </div>
                </div>
              </div>

              <button 
                onClick={handleSaveConfig}
                disabled={isSaving}
                style={{
                  marginTop: '0.5rem',
                  padding: '0.6rem 1rem',
                  background: 'var(--md-sys-color-primary)',
                  color: 'var(--md-sys-color-on-primary)',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontWeight: '600',
                  cursor: isSaving ? 'not-allowed' : 'pointer',
                  opacity: isSaving ? 0.7 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
              >
                {isSaving ? 'Saving...' : 'Save Configuration'}
              </button>

              {statusMessage && (
                <div style={{
                  padding: '0.75rem',
                  background: statusMessage.includes('Error') || statusMessage.includes('Warning') 
                    ? 'rgba(235, 87, 87, 0.1)' 
                    : 'var(--md-sys-color-surface-container-highest)',
                  color: statusMessage.includes('Error') || statusMessage.includes('Warning')
                    ? '#eb5757'
                    : 'var(--text-secondary)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  border: `1px solid ${statusMessage.includes('Error') || statusMessage.includes('Warning') ? 'rgba(235, 87, 87, 0.2)' : 'var(--md-sys-color-outline-variant)'}`
                }}>
                  {statusMessage}
                </div>
              )}

              {/* 💡 Senior Dev Note: Why does the API key input stay empty on reload?
                  The key is intentionally never returned by the GET /api/settings endpoint.
                  Returning secrets to the frontend is a security anti-pattern (it could be exposed 
                  to XSS or accidental logging). The client only needs to know 'has_api_key' to show 
                  the correct connection status. 
              */}
            </div>
          </div>

          <div className="surface-card" style={{ padding: '1.25rem', border: '1px solid var(--md-sys-color-outline-variant)', marginTop: '1.5rem' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '0.95rem' }}>Web Search Configuration</h4>
            <p style={{ margin: '0 0 1.25rem 0', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Tavily: https://tavily.com (free tier). Brave: https://brave.com/search/api/ (free tier). The key lives in server memory until restart — never returned to the browser.
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label htmlFor="searchProvider" style={{ display: 'block', fontWeight: '500', color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                  Search Provider
                </label>
                <select 
                  id="searchProvider" 
                  name="searchProvider" 
                  value={settings.searchProvider || 'tavily'} 
                  onChange={handleChange}
                  style={{ 
                    width: '100%', 
                    padding: '0.6rem 0.75rem', 
                    background: 'var(--md-sys-color-surface-container-high)', 
                    border: '1px solid var(--md-sys-color-outline-variant)', 
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    fontSize: '0.9rem',
                    outline: 'none'
                  }}
                >
                  <option value="tavily">Tavily</option>
                  <option value="brave">Brave</option>
                </select>
              </div>

              <div>
                <label htmlFor="searchApiKey" style={{ display: 'block', fontWeight: '500', color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                  API Key
                </label>
                <div style={{ position: 'relative' }}>
                  <input 
                    type={showSearchKey ? 'text' : 'password'} 
                    id="searchApiKey" 
                    name="searchApiKey" 
                    value={settings.searchApiKey || ''} 
                    onChange={handleChange}
                    placeholder="tvly-... or BSA..."
                    style={{ 
                      width: '100%', 
                      padding: '0.6rem 2.5rem 0.6rem 0.75rem', 
                      background: 'var(--md-sys-color-surface-container-high)', 
                      border: '1px solid var(--md-sys-color-outline-variant)', 
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--text-primary)',
                      fontSize: '0.9rem',
                      outline: 'none'
                    }}
                  />
                  <div 
                    onClick={() => setShowSearchKey(!showSearchKey)}
                    style={{ 
                      position: 'absolute', 
                      right: '0.75rem', 
                      top: '50%', 
                      transform: 'translateY(-50%)',
                      cursor: 'pointer',
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    title={showSearchKey ? "Hide API Key" : "Show API Key"}
                  >
                    {showSearchKey ? (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    )}
                  </div>
                </div>
              </div>

              <button 
                onClick={handleSaveSearchConfig}
                disabled={isSavingSearch}
                style={{
                  marginTop: '0.5rem',
                  padding: '0.6rem 1rem',
                  background: 'var(--md-sys-color-secondary)',
                  color: 'var(--md-sys-color-on-secondary)',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontWeight: '600',
                  cursor: isSavingSearch ? 'not-allowed' : 'pointer',
                  opacity: isSavingSearch ? 0.7 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
              >
                {isSavingSearch ? 'Saving...' : 'Save Configuration'}
              </button>

              {searchStatusMessage && (
                <div style={{
                  padding: '0.75rem',
                  background: searchStatusMessage.includes('Error') || searchStatusMessage.includes('Warning') 
                    ? 'rgba(235, 87, 87, 0.1)' 
                    : 'var(--md-sys-color-surface-container-highest)',
                  color: searchStatusMessage.includes('Error') || searchStatusMessage.includes('Warning')
                    ? '#eb5757'
                    : 'var(--text-secondary)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  border: `1px solid ${searchStatusMessage.includes('Error') || searchStatusMessage.includes('Warning') ? 'rgba(235, 87, 87, 0.2)' : 'var(--md-sys-color-outline-variant)'}`
                }}>
                  {searchStatusMessage}
                </div>
              )}
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
