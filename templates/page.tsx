'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  Search,
  Settings,
  Plus,
  Pin,
  Trash2,
  Edit3,
  Copy,
  Download,
  ExternalLink,
  BarChart3,
  Sparkles,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

// Import our new components
import SessionRail from '@/components/optimization/SessionRail';
import ChatThread from '@/components/optimization/ChatThread';
import ChatComposer from '@/components/optimization/ChatComposer';
import ContextPane from '@/components/optimization/ContextPane';

// Import the store
import { useOptimizerSessionsStore } from '@/store/optimizerSessionsStore';

// Import existing services (don't modify)
import { useSSEChat } from '@/lib/services/sse-chat';
import { promptService } from '@/lib/services/prompt-service';

const ChatOptimizerPage: React.FC = () => {
  const { service, isConnected } = useSSEChat();

  // Store state
  const {
    activeSessionId,
    sessions,
    lastActiveSessionId,
    createSession,
    setActiveSession,
    restoreNavigation
  } = useOptimizerSessionsStore();

  // Local state
  const [isLoading, setIsLoading] = useState(true);

  // Initialize on mount
  useEffect(() => {
    const initialize = async () => {
      try {
        // Restore navigation state
        restoreNavigation();

        // If no active session, create one or restore last active
        if (!activeSessionId) {
          if (lastActiveSessionId && sessions[lastActiveSessionId]) {
            setActiveSession(lastActiveSessionId);
          } else {
            // Create a new session
            createSession();
          }
        }

        setIsLoading(false);
      } catch (error) {
        console.error('Failed to initialize optimizer:', error);
        setIsLoading(false);
      }
    };

    initialize();
  }, [activeSessionId, lastActiveSessionId, sessions, createSession, setActiveSession, restoreNavigation]);

  // Handle session creation
  const handleCreateSession = useCallback(() => {
    createSession();
  }, [createSession]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 mx-auto mb-4">
            <Sparkles className="w-full h-full text-blue-500 animate-pulse" />
          </div>
          <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-300 mb-2">
            Loading Chat Optimizer
          </h2>
          <p className="text-slate-500 dark:text-slate-400">
            Restoring your sessions...
          </p>
        </motion.div>
      </div>
    );
  }

  const activeSession = activeSessionId ? sessions[activeSessionId] : null;

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 overflow-hidden">
      {/* Left Rail - Sessions */}
      <div className="w-80 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <SessionRail
          activeSessionId={activeSessionId}
          onCreateSession={handleCreateSession}
          onSelectSession={setActiveSession}
        />
      </div>

      {/* Center - Chat Thread */}
      <div className="flex-1 flex flex-col bg-white dark:bg-slate-800">
        <ChatThread
          session={activeSession}
          isConnected={isConnected}
        />
      </div>

      {/* Right Rail - Context & Tools */}
      <div className="w-96 border-l border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <ContextPane
          session={activeSession}
        />
      </div>
    </div>
  );
};

export default ChatOptimizerPage;
  });
  const [bulkStatus, setBulkStatus] = useState<BulkIngestStatus>({
    isRunning: false,
    progress: 0,
    processed: 0,
    total: 0,
    errors: 0,
    estimatedTimeRemaining: 0
  });
  const [lastOptimization] = useState<string>('');
  const [recentIntents] = useState<string[]>([]);

  // Check connection status
  useEffect(() => {
    // Stats updates simulation
    const updateStats = () => {
      setStats(prev => ({
        ...prev,
        totalPrompts: prev.totalPrompts + Math.floor(Math.random() * 5),
        optimizedToday: prev.optimizedToday + Math.floor(Math.random() * 3),
        avgResponseTime: 35 + Math.random() * 20,
        successRate: 92 + Math.random() * 8,
        activeConnections: Math.floor(Math.random() * 50) + 10
      }));
    };

    const statsInterval = setInterval(updateStats, 5000);

    return () => {
      clearInterval(statsInterval);
    };
  }, []);

  // Handle bulk ingest of 100k prompts
  const handleBulkIngest = async () => {
    if (bulkStatus.isRunning) {
      setBulkStatus(prev => ({ ...prev, isRunning: false }));
      return;
    }

    setBulkStatus(prev => ({ 
      ...prev, 
      isRunning: true, 
      progress: 0, 
      processed: 0, 
      total: 100000,
      errors: 0 
    }));

    try {
      // Generate sample prompts
      const prompts = promptService.generateSamplePrompts(100000);
      
      // Start bulk ingest with progress tracking
      const batchSize = 1000;
      let processed = 0;
      let errors = 0;

      for (let i = 0; i < prompts.length; i += batchSize) {
        if (!bulkStatus.isRunning) break; // Allow cancellation

        const batch = prompts.slice(i, i + batchSize);
        const startTime = Date.now();

        try {
          const result = await promptService.bulkIngestPrompts(batch, batchSize);
          processed += result.processed;
          errors += result.failed;
        } catch (error) {
          console.error('Batch failed:', error);
          errors += batch.length;
        }

        const progress = ((i + batchSize) / prompts.length) * 100;
        const avgTimePerBatch = Date.now() - startTime;
        const remainingBatches = Math.ceil((prompts.length - i - batchSize) / batchSize);
        const estimatedTimeRemaining = (remainingBatches * avgTimePerBatch) / 1000;

        setBulkStatus(prev => ({
          ...prev,
          progress: Math.min(progress, 100),
          processed,
          errors,
          estimatedTimeRemaining
        }));

        // Small delay to prevent overwhelming
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      setBulkStatus(prev => ({ 
        ...prev, 
        isRunning: false, 
        progress: 100,
        estimatedTimeRemaining: 0 
      }));

    } catch (error) {
      console.error('Bulk ingest failed:', error);
      setBulkStatus(prev => ({ ...prev, isRunning: false }));
    }
  };

  // Handle prompt optimization
  const handlePromptOptimized = (optimized: unknown) => {
    console.log('Prompt optimized:', optimized);
    setStats(prev => ({
      ...prev,
      optimizedToday: prev.optimizedToday + 1,
      avgResponseTime: prev.avgResponseTime
    }));
  };

  // Handle intent detection
  const handleIntentDetected = (intent: unknown) => {
    console.log('Intent detected:', intent);
  };

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ElementType;
    color: string;
    trend?: number;
  }> = ({ title, value, icon: Icon, color, trend }) => (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      className="bg-white p-6 rounded-xl shadow-lg border border-gray-100"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {trend !== undefined && (
            <p className={`text-sm mt-1 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend >= 0 ? '+' : ''}{trend.toFixed(1)}% from last hour
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Brain className="w-8 h-8 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">
                Prompt Optimization Platform
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'SSE Connected' : 'Reconnecting...'}
                </span>
                {isConnected && (
                  <Activity className="w-4 h-4 text-green-500" />
                )}
              </div>
              
              <Settings className="w-5 h-5 text-gray-400 cursor-pointer hover:text-gray-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Stats Dashboard */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard
            title="Total Prompts"
            value={stats.totalPrompts}
            icon={Database}
            color="bg-blue-500"
            trend={5.2}
          />
          <StatCard
            title="Optimized Today"
            value={stats.optimizedToday}
            icon={Zap}
            color="bg-green-500"
            trend={12.3}
          />
          <StatCard
            title="Avg Response Time"
            value={`${stats.avgResponseTime.toFixed(0)}ms`}
            icon={Activity}
            color="bg-purple-500"
            trend={-2.1}
          />
          <StatCard
            title="Success Rate"
            value={`${stats.successRate.toFixed(1)}%`}
            icon={CheckCircle}
            color="bg-emerald-500"
            trend={0.8}
          />
          <StatCard
            title="Active Users"
            value={stats.activeConnections}
            icon={MessageSquare}
            color="bg-orange-500"
            trend={8.4}
          />
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[
                { id: 'search', name: 'Smart Search', icon: Search },
                { id: 'chat', name: 'Chat Optimizer', icon: MessageSquare },
                { id: 'bulk', name: 'Bulk Ingest', icon: Upload },
                { id: 'analytics', name: 'Analytics', icon: BarChart3 },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            <AnimatePresence mode="wait">
              {activeTab === 'search' && (
                <motion.div
                  key="search"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900 mb-2">
                        Intelligent Prompt Search & Optimization
                      </h2>
                      <p className="text-gray-600">
                        Type your intent and get real-time optimized prompts with AI-powered suggestions.
                      </p>
                    </div>
                    
                    <AnimatedSuggestionBox
                      onPromptSelect={(prompt) => {
                        console.log('Selected prompt:', prompt);
                      }}
                      onIntentDetected={handleIntentDetected}
                    />
                    
                    {/* Recent Intents */}
                    {recentIntents.length > 0 && (
                      <div className="mt-8">
                        <h3 className="text-md font-medium text-gray-900 mb-4">Recent Intent Analysis</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {recentIntents.map((intent, index) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="bg-blue-50 border border-blue-200 rounded-lg p-4"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium text-blue-900">
                                  {intent.detectedIntent}
                                </span>
                                <span className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                  {Math.round(intent.confidence * 100)}%
                                </span>
                              </div>
                              <div className="text-sm text-blue-700">
                                Category: {intent.category}
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {activeTab === 'chat' && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                  className="h-96"
                >
                  <SSEChatInterface 
                    enableOptimization={true}
                    enableAnalytics={true}
                    onPromptOptimized={handlePromptOptimized} 
                  />
                </motion.div>
              )}

              {activeTab === 'bulk' && (
                <motion.div
                  key="bulk"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900 mb-2">
                        Bulk Prompt Ingestion
                      </h2>
                      <p className="text-gray-600">
                        Ingest 100,000 prompts into the database with LangChain integration and vector embeddings.
                      </p>
                    </div>

                    {/* Bulk Ingest Controls */}
                    <div className="bg-gray-50 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="font-medium text-gray-900">Bulk Ingest Status</h3>
                          <p className="text-sm text-gray-600">
                            {bulkStatus.isRunning ? 'Processing...' : 'Ready to process 100,000 prompts'}
                          </p>
                        </div>
                        
                        <button
                          onClick={handleBulkIngest}
                          disabled={bulkStatus.isRunning && bulkStatus.progress === 100}
                          className={`px-6 py-3 rounded-lg font-medium flex items-center space-x-2 transition-colors ${
                            bulkStatus.isRunning
                              ? 'bg-red-500 hover:bg-red-600 text-white'
                              : 'bg-blue-500 hover:bg-blue-600 text-white'
                          }`}
                        >
                          {bulkStatus.isRunning ? (
                            <>
                              <Pause className="w-4 h-4" />
                              <span>Stop Ingest</span>
                            </>
                          ) : (
                            <>
                              <Play className="w-4 h-4" />
                              <span>Start Bulk Ingest</span>
                            </>
                          )}
                        </button>
                      </div>

                      {/* Progress Bar */}
                      {(bulkStatus.isRunning || bulkStatus.progress > 0) && (
                        <div className="space-y-3">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${bulkStatus.progress}%` }}
                              transition={{ duration: 0.5 }}
                              className="bg-blue-500 h-2 rounded-full"
                            />
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">Progress:</span>
                              <span className="ml-2 font-medium">{bulkStatus.progress.toFixed(1)}%</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Processed:</span>
                              <span className="ml-2 font-medium">{bulkStatus.processed.toLocaleString()}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Errors:</span>
                              <span className="ml-2 font-medium text-red-600">{bulkStatus.errors}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">ETA:</span>
                              <span className="ml-2 font-medium">
                                {bulkStatus.estimatedTimeRemaining > 0 
                                  ? `${Math.ceil(bulkStatus.estimatedTimeRemaining)}s`
                                  : 'Complete'
                                }
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'analytics' && (
                <motion.div
                  key="analytics"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900 mb-2">
                        Performance Analytics
                      </h2>
                      <p className="text-gray-600">
                        Real-time performance metrics and optimization insights.
                      </p>
                    </div>

                    {/* Last Optimization */}
                    {lastOptimization && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                        <h3 className="font-medium text-green-900 mb-3 flex items-center">
                          <CheckCircle className="w-5 h-5 mr-2" />
                          Latest Optimization
                        </h3>
                        <div className="space-y-2">
                          <div className="text-sm">
                            <span className="text-green-700">Optimized Prompt:</span>
                            <p className="text-green-900 mt-1 font-medium">
                              {lastOptimization.optimizedPrompt}
                            </p>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-green-700">
                            <span>Confidence: {Math.round(lastOptimization.confidence * 100)}%</span>
                            <span>Processing Time: {lastOptimization.processingTime}ms</span>
                            <span>Alternatives: {lastOptimization.alternatives.length}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Performance Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-white border border-gray-200 rounded-lg p-6">
                        <h3 className="font-medium text-gray-900 mb-4">Response Time Distribution</h3>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">&lt; 25ms</span>
                            <span className="text-sm font-medium text-green-600">65%</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">25-50ms</span>
                            <span className="text-sm font-medium text-blue-600">28%</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">&gt; 50ms</span>
                            <span className="text-sm font-medium text-orange-600">7%</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-white border border-gray-200 rounded-lg p-6">
                        <h3 className="font-medium text-gray-900 mb-4">Intent Categories</h3>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Creative Writing</span>
                            <span className="text-sm font-medium">32%</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Business</span>
                            <span className="text-sm font-medium">25%</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Technical</span>
                            <span className="text-sm font-medium">18%</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Educational</span>
                            <span className="text-sm font-medium">15%</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Other</span>
                            <span className="text-sm font-medium">10%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromptOptimizationDashboard;
