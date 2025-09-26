/**
 * RAG Agent Frontend Integration Components
 * Minimal additions to existing chat UI for RAG features
 */

import React, { useState, useEffect, useCallback } from 'react';

// RAG Mode Selector Component
export const RAGModeSelector = ({ mode, onModeChange, budget, onBudgetChange }) => {
  return (
    <div className="rag-controls">
      <div className="mode-selector">
        <label className="text-sm font-medium text-gray-700">Optimization Mode:</label>
        <div className="flex gap-2 mt-1">
          <button
            className={`px-3 py-1 text-xs rounded-full ${
              mode === 'fast' 
                ? 'bg-blue-100 text-blue-800 border border-blue-200' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => onModeChange('fast')}
          >
            ⚡ Fast (1 credit)
          </button>
          <button
            className={`px-3 py-1 text-xs rounded-full ${
              mode === 'deep' 
                ? 'bg-purple-100 text-purple-800 border border-purple-200' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => onModeChange('deep')}
          >
            🧠 Deep (3 credits)
          </button>
        </div>
      </div>
      
      <div className="budget-selector">
        <label className="text-sm font-medium text-gray-700">Budget:</label>
        <select 
          className="mt-1 text-xs border rounded px-2 py-1"
          value={budget}
          onChange={(e) => onBudgetChange(e.target.value)}
        >
          <option value="basic">Basic (5 credits max)</option>
          <option value="extended">Extended (10 credits max)</option>
        </select>
      </div>
    </div>
  );
};

// RAG Pill Component (shows when RAG is active)
export const RAGPill = ({ isActive, citations, onToggleCitations }) => {
  if (!isActive) return null;

  return (
    <div className="flex items-center gap-2">
      <div className="rag-pill">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 border border-blue-200">
          <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          RAG Agent
        </span>
      </div>
      
      {citations.length > 0 && (
        <button
          className="citations-button text-xs text-blue-600 hover:text-blue-800 underline"
          onClick={onToggleCitations}
        >
          {citations.length} source{citations.length !== 1 ? 's' : ''}
        </button>
      )}
    </div>
  );
};

// Citations Popover Component
export const CitationsPopover = ({ citations, isOpen, onClose }) => {
  if (!isOpen || citations.length === 0) return null;

  return (
    <div className="citations-popover absolute z-50 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-semibold text-gray-800">Sources Used</h3>
        <button 
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
      
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {citations.map((citation, index) => (
          <div key={citation.id} className="citation-item">
            <div className="flex items-start gap-2">
              <div className="citation-score">
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {index + 1}
                </span>
              </div>
              <div className="citation-content flex-1">
                <div className="citation-header">
                  <h4 className="text-sm font-medium text-gray-800 truncate">
                    {citation.title}
                  </h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="source-tag text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                      {citation.source}
                    </span>
                    <span className="relevance-score text-xs text-gray-500">
                      {Math.round(citation.score * 100)}% match
                    </span>
                  </div>
                </div>
                <p className="citation-snippet text-xs text-gray-600 mt-2 line-clamp-2">
                  {citation.snippet}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Enhanced Chat Input with RAG Integration
export const EnhancedChatInput = ({ 
  message, 
  onMessageChange, 
  onSend, 
  onRAGOptimize,
  isLoading,
  ragMode,
  onRAGModeChange,
  budget,
  onBudgetChange 
}) => {
  const [showRAGControls, setShowRAGControls] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (showRAGControls) {
      onRAGOptimize(message, ragMode, budget);
    } else {
      onSend(message);
    }
  };

  return (
    <div className="enhanced-chat-input">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="input-wrapper relative">
          <textarea
            value={message}
            onChange={(e) => onMessageChange(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Type your message or prompt to optimize..."
            rows={3}
            disabled={isLoading}
          />
          
          <div className="input-controls absolute bottom-2 right-2 flex gap-2">
            <button
              type="button"
              className={`rag-toggle text-xs px-2 py-1 rounded ${
                showRAGControls 
                  ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              onClick={() => setShowRAGControls(!showRAGControls)}
            >
              🧠 RAG
            </button>
            
            <button
              type="submit"
              disabled={!message.trim() || isLoading}
              className="send-button bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '...' : showRAGControls ? '✨ Optimize' : '📤 Send'}
            </button>
          </div>
        </div>
        
        {showRAGControls && (
          <RAGModeSelector
            mode={ragMode}
            onModeChange={onRAGModeChange}
            budget={budget}
            onBudgetChange={onBudgetChange}
          />
        )}
      </form>
    </div>
  );
};

// Message Component with RAG Support
export const RAGMessage = ({ message, isBot }) => {
  const [showCitations, setShowCitations] = useState(false);
  const citations = message.citations || [];
  const isRAGResponse = message.type === 'rag_optimization' || citations.length > 0;

  return (
    <div className={`message ${isBot ? 'bot-message' : 'user-message'}`}>
      <div className="message-content">
        <div className="message-text">
          {message.content}
        </div>
        
        {isRAGResponse && (
          <div className="rag-metadata mt-2">
            <RAGPill
              isActive={true}
              citations={citations}
              onToggleCitations={() => setShowCitations(!showCitations)}
            />
            
            {message.diff_summary && (
              <div className="diff-summary mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                <strong>Improvements:</strong>
                <div className="whitespace-pre-line">{message.diff_summary}</div>
              </div>
            )}
            
            <div className="relative">
              <CitationsPopover
                citations={citations}
                isOpen={showCitations}
                onClose={() => setShowCitations(false)}
              />
            </div>
          </div>
        )}
      </div>
      
      {message.usage && (
        <div className="usage-info mt-1 text-xs text-gray-500">
          Used {message.usage.credits} credit{message.usage.credits !== 1 ? 's' : ''} • 
          {message.usage.tokens_in + message.usage.tokens_out} tokens
        </div>
      )}
    </div>
  );
};

// Main Chat Component Integration Example
export const RAGEnabledChat = () => {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [ragMode, setRAGMode] = useState('fast');
  const [budget, setBudget] = useState('basic');
  const [websocket, setWebsocket] = useState(null);

  // WebSocket setup (using existing connection)
  useEffect(() => {
    // Assume you have existing WebSocket connection
    // Add RAG-specific message handlers
    if (websocket) {
      const handleRAGMessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'agent.start':
            setIsLoading(true);
            break;
            
          case 'agent.token':
            // Handle streaming content
            updateStreamingMessage(data.run_id, data.content);
            break;
            
          case 'agent.citations':
            // Store citations for the message
            updateMessageCitations(data.run_id, data.citations);
            break;
            
          case 'agent.done':
            setIsLoading(false);
            addRAGMessage(data);
            break;
            
          case 'agent.error':
            setIsLoading(false);
            showError(data.message);
            break;
        }
      };

      websocket.addEventListener('message', handleRAGMessage);
      return () => websocket.removeEventListener('message', handleRAGMessage);
    }
  }, [websocket]);

  const handleRAGOptimize = (prompt, mode, budgetLevel) => {
    if (!websocket) return;

    websocket.send(JSON.stringify({
      type: 'agent_optimize',
      original: prompt,
      mode,
      context: { intent: 'general' },
      budget: budgetLevel === 'basic' ? { max_credits: 5 } : { max_credits: 10 }
    }));

    setCurrentMessage('');
  };

  const addRAGMessage = (data) => {
    const newMessage = {
      id: data.run_id,
      content: data.optimized,
      type: 'rag_optimization',
      citations: data.citations || [],
      diff_summary: data.diff_summary,
      usage: data.usage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
  };

  return (
    <div className="rag-enabled-chat">
      <div className="messages-container">
        {messages.map(message => (
          <RAGMessage 
            key={message.id} 
            message={message} 
            isBot={message.type === 'rag_optimization'} 
          />
        ))}
        
        {isLoading && (
          <div className="loading-message">
            <div className="flex items-center gap-2">
              <div className="loading-spinner animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span className="text-sm text-gray-600">RAG Agent is optimizing your prompt...</span>
            </div>
          </div>
        )}
      </div>
      
      <EnhancedChatInput
        message={currentMessage}
        onMessageChange={setCurrentMessage}
        onSend={(msg) => {/* handle regular chat */}}
        onRAGOptimize={handleRAGOptimize}
        isLoading={isLoading}
        ragMode={ragMode}
        onRAGModeChange={setRAGMode}
        budget={budget}
        onBudgetChange={setBudget}
      />
    </div>
  );
};

// CSS additions (add to your existing styles)
const ragStyles = `
.rag-controls {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.citations-popover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.citation-item {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
}

.citation-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.loading-spinner {
  border-top-color: transparent;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
`;

export default RAGEnabledChat;