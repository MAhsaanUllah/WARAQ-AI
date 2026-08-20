/**
 * API client for Waraq AI
 */

/**
 * Uploads multiple documents to the server for processing.
 * @param {File[]} files 
 * @returns {Promise<Object>} The response containing batch details
 */
export async function uploadDocuments(files, token = null) {
  const formData = new FormData();
  // Append all files to the 'files' field
  if (files && files.length > 0) {
    Array.from(files).forEach(file => formData.append('files', file));
  }

  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch('/api/upload-docs', {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = 'Upload failed';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch (e) {
      // Ignored
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Connects to the streaming query endpoint and manages events.
 * 
 * @param {string} question The query string
 * @param {boolean} useWebSearch Whether to enable web search
 * @param {Function} onEvent Called with ('status'|'answer_delta', data)
 * @param {Function} onError Called with an error message
 * @param {Function} onDone Called with final sources data
 * @returns {Function} A function to abort the stream
 */
export function streamQuery(question, settings, useWebSearch, documentIds, onEvent, onError, onDone, token = null) {
  const topKCandidates = settings?.topKCandidates || 25;
  const topKFinal = settings?.topKFinal || 5;
  
  let url = `/api/stream-query?question=${encodeURIComponent(question)}&top_k_candidates=${topKCandidates}&top_k_final=${topKFinal}`;
  
  if (useWebSearch) {
    url += '&use_web_search=true';
  }
  
  if (documentIds && documentIds.length > 0) {
    url += `&document_ids=${encodeURIComponent(documentIds.join(','))}`;
  }
  // For SSE EventSource, we must pass the token in the URL query params
  // because EventSource API doesn't support custom headers.
  if (arguments.length > 7 && typeof arguments[7] === 'string') {
    url += `&token=${encodeURIComponent(arguments[7])}`;
  }

  const eventSource = new EventSource(url);
  
  eventSource.addEventListener('status', (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent('status', data);
    } catch (err) {
      console.error('Failed to parse status event', err);
    }
  });

  eventSource.addEventListener('answer_delta', (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent('answer_delta', data);
    } catch (err) {
      console.error('Failed to parse answer_delta event', err);
    }
  });

  eventSource.addEventListener('done', (e) => {
    try {
      const data = JSON.parse(e.data);
      onDone(data);
    } catch (err) {
      console.error('Failed to parse done event', err);
    } finally {
      eventSource.close();
    }
  });

  // Handle explicit error events or network disconnects
  eventSource.onerror = (e) => {
    // If the server sends an event with name 'error' we might need a specific listener instead,
    // but typically EventSource calls onerror for network issues.
    onError('Connection error during streaming or stream closed.');
    eventSource.close();
  };
  
  // Custom error event if backend emits 'event: error'
  eventSource.addEventListener('error', (e) => {
    try {
      const data = JSON.parse(e.data);
      onError(data.detail || 'Server sent an error');
    } catch (err) {
      onError('Server sent an unknown error');
    }
    eventSource.close();
  });

  return () => {
    eventSource.close();
  };
}

/** 
 * Fetch the current LLM provider and whether a key is set. 
 * Never returns the key. 
 */
export async function getLLMSettings(token = null) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch('/api/settings', { headers });
  if (!response.ok) {
    let errorDetail = 'Failed to load settings';
    try {
      errorDetail = (await response.json()).detail || errorDetail;
    } catch (e) {}
    throw new Error(errorDetail);
  }
  return response.json();
}

/** 
 * Save the BYOK provider + API key (in-memory on the backend). 
 */
export async function setLLMSettings({ provider, apiKey }, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch('/api/settings', {
    method: 'PUT',
    headers,
    body: JSON.stringify({ provider, api_key: apiKey }),
  });
  
  if (!response.ok) {
    let errorDetail = 'Failed to save settings';
    try {
      errorDetail = (await response.json()).detail || errorDetail;
    } catch (e) {}
    throw new Error(errorDetail);
  }
  return response.json();
}

/** 
 * Save the Web Search provider + API key (in-memory on the backend). 
 */
export async function setSearchSettings({ provider, apiKey }, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch('/api/settings/search', {
    method: 'PUT',
    headers,
    body: JSON.stringify({ provider, api_key: apiKey }),
  });
  
  if (!response.ok) {
    let errorDetail = 'Failed to save search settings';
    try {
      errorDetail = (await response.json()).detail || errorDetail;
    } catch (e) {}
    throw new Error(errorDetail);
  }
  return response.json();
}
