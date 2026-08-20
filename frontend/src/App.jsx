import React, { useState, useEffect } from 'react';
import SidebarLeft from './components/SidebarLeft';
import SidebarRight from './components/SidebarRight';
import UploadPage from './components/UploadPage';
import QueryPage from './components/QueryPage';
import SettingsPage from './components/SettingsPage';

function App() {
  const [activeTab, setActiveTab] = useState('query');
  
  // Local storage for history since backend doesn't support it yet
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('waraq_sessions');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return [];
  });
  
  const [activeSessionId, setActiveSessionId] = useState(() => {
    return sessions.length > 0 ? sessions[0].id : Date.now();
  });

  // Settings state
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('waraq_settings');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return { topKCandidates: 25, topKFinal: 5 };
  });

  useEffect(() => {
    localStorage.setItem('waraq_sessions', JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    localStorage.setItem('waraq_settings', JSON.stringify(settings));
  }, [settings]);

  const handleNewChat = () => {
    setActiveTab('query');
    setActiveSessionId(Date.now());
  };

  const handleUpdateSession = (id, history) => {
    setSessions(prev => {
      const existingIdx = prev.findIndex(s => s.id === id);
      const title = history.find(m => m.role === 'user' && !m.text.startsWith('📎 Uploading'))?.text || 'New Chat';
      
      if (existingIdx >= 0) {
        const next = [...prev];
        next[existingIdx] = { ...next[existingIdx], title, history, updatedAt: Date.now() };
        return next;
      } else {
        return [{ id, title, history, updatedAt: Date.now() }, ...prev];
      }
    });
  };

  const handleSelectSession = (id) => {
    setActiveTab('query');
    setActiveSessionId(id);
  };

  const handleDeleteHistory = () => {
    if (window.confirm('Are you sure you want to delete all chat history?')) {
      setSessions([]);
      setActiveSessionId(Date.now());
    }
  };

  return (
    <div className="app-container">
      {/* Left Column */}
      <SidebarLeft activeTab={activeTab} setActiveTab={setActiveTab} onNewChat={handleNewChat} />

      {/* Center Column */}
      <div className="main-content">
        {activeTab === 'upload' && (
          <UploadPage onUploadSuccess={() => setActiveTab('query')} />
        )}
        
        {activeTab === 'settings' && (
          <SettingsPage settings={settings} setSettings={setSettings} />
        )}

        {activeTab === 'query' && (
          <QueryPage 
            key={activeSessionId} 
            sessionId={activeSessionId}
            initialHistory={sessions.find(s => s.id === activeSessionId)?.history || null}
            onUpdateSession={handleUpdateSession}
            settings={settings}
          />
        )}
      </div>

      {/* Right Column */}
      <SidebarRight 
        sessions={sessions} 
        activeSessionId={activeSessionId} 
        onSelectSession={handleSelectSession} 
        onDeleteHistory={handleDeleteHistory}
      />
    </div>
  );
}

export default App;
