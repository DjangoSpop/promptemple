// 🏛️ RAG Agent Interface - Sprint 1 Implementation
// File: src/components/optimization/RAGAgentInterface.tsx

import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Card } from '@/components/ui/card-unified';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Sparkles, 
  Brain, 
  Zap, 
  Book, 
  Target, 
  TrendingUp,
  CheckCircle,
  AlertTriangle,
  CreditCard,
  Eye,
  Copy,
  Download
} from 'lucide-react';

// 🏺 RAG Agent Store with SSE Integration
interface RAGAgentState {
  // Core state
  mode: 'standard' | 'rag-fast' | 'rag-deep';
  originalPrompt: string;
  optimizedPrompt: string;
  isOptimizing: boolean;
  
  // RAG specific
  citations: Citation[];
  diffSummary: DiffPoint[];
  budgetUsed: BudgetUsage;
  agentProgress: AgentStep[];
  
  // SSE streaming state
  isStreaming: boolean;
  currentStep: string;
  streamingTokens: string;
  
  // Actions
  setMode: (mode: RAGAgentState['mode']) => void;
  setOriginalPrompt: (prompt: string) => void;
  startOptimization: (sessionId: string, prompt: string) => void;
  handleSSEEvent: (event: RAGSSEEvent) => void;
  resetState: () => void;
}

interface Citation {
  id: string;
  title: string;
  source: string;
  score: number;
  snippet: string;
  type: 'template' | 'document' | 'example';
}

interface DiffPoint {
  type: 'addition' | 'improvement' | 'structure';
  description: string;
  impact: 'high' | 'medium' | 'low';
}

interface BudgetUsage {
  tokens_in: number;
  tokens_out: number;
  credits: number;
  max_credits: number;
  remaining_credits: number;
}

interface AgentStep {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'complete' | 'error';
  timestamp: string;
  duration_ms?: number;
}

interface RAGSSEEvent {
  type: 'agent.start' | 'agent.step' | 'agent.token' | 'agent.citations' | 'agent.done' | 'agent.error';
  data: any;
}

const useRAGAgentStore = create<RAGAgentState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    mode: 'standard',
    originalPrompt: '',
    optimizedPrompt: '',
    isOptimizing: false,
    citations: [],
    diffSummary: [],
    budgetUsed: {
      tokens_in: 0,
      tokens_out: 0,
      credits: 0,
      max_credits: 5,
      remaining_credits: 5
    },
    agentProgress: [],
    isStreaming: false,
    currentStep: '',
    streamingTokens: '',
    
    // Actions
    setMode: (mode) => set({ mode }),
    setOriginalPrompt: (prompt) => set({ originalPrompt: prompt }),
    
    startOptimization: (sessionId, prompt) => {
      set({
        isOptimizing: true,
        originalPrompt: prompt,
        optimizedPrompt: '',
        citations: [],
        diffSummary: [],
        agentProgress: [],
        streamingTokens: '',
        isStreaming: false
      });
    },
    
    handleSSEEvent: (event) => {
      const state = get();
      
      switch (event.type) {
        case 'agent.start':
          set({
            isStreaming: true,
            currentStep: 'Initializing RAG Agent...',
            agentProgress: [
              { id: '1', name: 'Knowledge Retrieval', status: 'active', timestamp: new Date().toISOString() },
              { id: '2', name: 'Context Analysis', status: 'pending', timestamp: new Date().toISOString() },
              { id: '3', name: 'Optimization Generation', status: 'pending', timestamp: new Date().toISOString() },
              { id: '4', name: 'Quality Validation', status: 'pending', timestamp: new Date().toISOString() }
            ]
          });
          break;
          
        case 'agent.step':
          set({
            currentStep: event.data.step_name,
            agentProgress: state.agentProgress.map(step => 
              step.id === event.data.step_id 
                ? { ...step, status: event.data.status, duration_ms: event.data.duration_ms }
                : step
            )
          });
          break;
          
        case 'agent.token':
          set({
            streamingTokens: state.streamingTokens + event.data.token
          });
          break;
          
        case 'agent.citations':
          set({
            citations: event.data.citations
          });
          break;
          
        case 'agent.done':
          set({
            isOptimizing: false,
            isStreaming: false,
            optimizedPrompt: event.data.optimized,
            diffSummary: event.data.diff_summary,
            budgetUsed: event.data.usage,
            agentProgress: state.agentProgress.map(step => ({ ...step, status: 'complete' }))
          });
          break;
          
        case 'agent.error':
          set({
            isOptimizing: false,
            isStreaming: false,
            currentStep: `Error: ${event.data.message}`
          });
          break;
      }
    },
    
    resetState: () => set({
      originalPrompt: '',
      optimizedPrompt: '',
      citations: [],
      diffSummary: [],
      agentProgress: [],
      streamingTokens: '',
      isStreaming: false,
      isOptimizing: false
    })
  }))
);

// 🌊 SSE Hook for RAG Agent
const useRAGSSE = (sessionId: string) => {
  const handleSSEEvent = useRAGAgentStore(state => state.handleSSEEvent);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    // Connect to RAG agent SSE stream
    const eventSource = new EventSource(`/api/v2/ai/agent/stream/${sessionId}/`);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('agent.start', (event) => {
      handleSSEEvent({ type: 'agent.start', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('agent.step', (event) => {
      handleSSEEvent({ type: 'agent.step', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('agent.token', (event) => {
      handleSSEEvent({ type: 'agent.token', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('agent.citations', (event) => {
      handleSSEEvent({ type: 'agent.citations', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('agent.done', (event) => {
      handleSSEEvent({ type: 'agent.done', data: JSON.parse(event.data) });
    });

    eventSource.addEventListener('agent.error', (event) => {
      handleSSEEvent({ type: 'agent.error', data: JSON.parse(event.data) });
    });

    return () => {
      eventSource.close();
    };
  }, [sessionId, handleSSEEvent]);

  return {
    disconnect: () => eventSourceRef.current?.close()
  };
};

// 🎯 Mode Selection Component
const RAGModeToggle = () => {
  const { mode, setMode, budgetUsed } = useRAGAgentStore();
  
  const modes = [
    {
      id: 'standard' as const,
      name: 'Standard',
      icon: Target,
      description: 'Basic optimization',
      credits: 1,
      speed: 'Fast',
      quality: 'Good'
    },
    {
      id: 'rag-fast' as const,
      name: 'RAG Fast',
      icon: Zap,
      description: 'AI-enhanced with knowledge retrieval',
      credits: 3,
      speed: 'Medium',
      quality: 'Excellent'
    },
    {
      id: 'rag-deep' as const,
      name: 'RAG Deep',
      icon: Brain,
      description: 'Comprehensive analysis with citations',
      credits: 5,
      speed: 'Slower',
      quality: 'Premium'
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-fg">Optimization Mode</h3>
        <div className="flex items-center gap-2">
          <CreditCard className="h-4 w-4 text-accent" />
          <span className="text-sm text-fg/70">
            {budgetUsed.remaining_credits} credits remaining
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {modes.map((modeOption) => {
          const Icon = modeOption.icon;
          const isSelected = mode === modeOption.id;
          const canAfford = budgetUsed.remaining_credits >= modeOption.credits;
          
          return (
            <Card 
              key={modeOption.id}
              variant={isSelected ? "temple" : "default"}
              className={`cursor-pointer transition-all duration-200 ${
                isSelected ? 'ring-2 ring-accent pharaoh-glow' : ''
              } ${!canAfford ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={() => canAfford && setMode(modeOption.id)}
            >
              <div className="flex flex-col items-center text-center space-y-3 p-4">
                <Icon className={`h-8 w-8 ${isSelected ? 'text-accent' : 'text-fg/70'}`} />
                <div>
                  <h4 className="font-semibold text-fg">{modeOption.name}</h4>
                  <p className="text-sm text-fg/60 mt-1">{modeOption.description}</p>
                </div>
                <div className="flex items-center gap-4 text-xs text-fg/70">
                  <span>⚡ {modeOption.speed}</span>
                  <span>🎯 {modeOption.quality}</span>
                  <Badge variant="secondary">{modeOption.credits} credits</Badge>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

// 📊 Agent Progress Tracker
const AgentProgressTracker = () => {
  const { agentProgress, currentStep, isStreaming } = useRAGAgentStore();
  
  if (agentProgress.length === 0) return null;
  
  const completedSteps = agentProgress.filter(step => step.status === 'complete').length;
  const progressPercent = (completedSteps / agentProgress.length) * 100;
  
  return (
    <Card variant="temple" className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-fg">RAG Agent Progress</h3>
        <Badge variant={isStreaming ? "default" : "secondary"}>
          {isStreaming ? 'Active' : 'Complete'}
        </Badge>
      </div>
      
      <Progress value={progressPercent} className="w-full" />
      
      <div className="space-y-2">
        {agentProgress.map((step, index) => {
          const Icon = step.status === 'complete' ? CheckCircle :
                      step.status === 'active' ? Sparkles :
                      step.status === 'error' ? AlertTriangle : Target;
                      
          return (
            <div key={step.id} className="flex items-center gap-3 p-2 rounded">
              <Icon className={`h-4 w-4 ${
                step.status === 'complete' ? 'text-green-500' :
                step.status === 'active' ? 'text-accent animate-pulse' :
                step.status === 'error' ? 'text-red-500' :
                'text-fg/30'
              }`} />
              <span className={`text-sm ${
                step.status === 'active' ? 'text-fg font-medium' : 'text-fg/70'
              }`}>
                {step.name}
                {step.duration_ms && (
                  <span className="text-xs text-fg/50 ml-2">
                    ({step.duration_ms}ms)
                  </span>
                )}
              </span>
            </div>
          );
        })}
      </div>
      
      {currentStep && isStreaming && (
        <div className="flex items-center gap-2 p-3 bg-accent/10 rounded-lg">
          <Sparkles className="h-4 w-4 text-accent animate-pulse" />
          <span className="text-sm text-fg">{currentStep}</span>
        </div>
      )}
    </Card>
  );
};

// 📚 Citations Panel
const CitationsPanel = () => {
  const { citations } = useRAGAgentStore();
  
  if (citations.length === 0) return null;
  
  return (
    <Card variant="temple" className="space-y-4">
      <div className="flex items-center gap-2">
        <Book className="h-5 w-5 text-accent" />
        <h3 className="text-lg font-semibold text-fg">Knowledge Sources</h3>
        <Badge variant="secondary">{citations.length} citations</Badge>
      </div>
      
      <ScrollArea className="max-h-64">
        <div className="space-y-3">
          {citations.map((citation) => (
            <div key={citation.id} className="border border-border rounded-lg p-3 hover:bg-card/50 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-fg text-sm">{citation.title}</h4>
                    <Badge variant="outline" className="text-xs">
                      {citation.type}
                    </Badge>
                  </div>
                  <p className="text-xs text-fg/60 mb-2">{citation.source}</p>
                  <p className="text-sm text-fg/80 leading-relaxed">{citation.snippet}</p>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <div className="text-xs font-mono bg-accent/20 text-accent px-2 py-1 rounded">
                    {(citation.score * 100).toFixed(0)}%
                  </div>
                  <Button size="sm" variant="ghost" className="h-6 w-6 p-0">
                    <Eye className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </Card>
  );
};

// 📈 Diff Summary Component
const DiffSummary = () => {
  const { diffSummary, originalPrompt, optimizedPrompt } = useRAGAgentStore();
  
  if (diffSummary.length === 0 || !optimizedPrompt) return null;
  
  const impactColors = {
    high: 'text-green-600 bg-green-50 border-green-200',
    medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    low: 'text-blue-600 bg-blue-50 border-blue-200'
  };
  
  return (
    <Card variant="temple" className="space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-accent" />
        <h3 className="text-lg font-semibold text-fg">Optimization Summary</h3>
      </div>
      
      <div className="space-y-3">
        {diffSummary.map((diff, index) => (
          <div key={index} className={`p-3 rounded-lg border ${impactColors[diff.impact]}`}>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline" className="text-xs capitalize">
                {diff.type}
              </Badge>
              <Badge variant="outline" className="text-xs capitalize">
                {diff.impact} impact
              </Badge>
            </div>
            <p className="text-sm">{diff.description}</p>
          </div>
        ))}
      </div>
      
      <div className="pt-4 border-t border-border">
        <Button className="w-full" variant="default">
          <CheckCircle className="h-4 w-4 mr-2" />
          Accept as Best Prompt
        </Button>
      </div>
    </Card>
  );
};

// 🎛️ Budget Tracker
const BudgetTracker = () => {
  const { budgetUsed } = useRAGAgentStore();
  
  const usagePercent = (budgetUsed.credits / budgetUsed.max_credits) * 100;
  
  return (
    <Card variant="default" className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-fg">Credit Usage</h4>
        <span className="text-sm text-fg/70">
          {budgetUsed.credits}/{budgetUsed.max_credits}
        </span>
      </div>
      
      <Progress value={usagePercent} className="w-full" />
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-fg/60">Tokens In:</span>
          <div className="font-mono text-fg">{budgetUsed.tokens_in.toLocaleString()}</div>
        </div>
        <div>
          <span className="text-fg/60">Tokens Out:</span>
          <div className="font-mono text-fg">{budgetUsed.tokens_out.toLocaleString()}</div>
        </div>
      </div>
    </Card>
  );
};

// 🏛️ Main RAG Agent Interface
export const RAGAgentInterface = () => {
  const {
    mode,
    originalPrompt,
    optimizedPrompt,
    isOptimizing,
    streamingTokens,
    startOptimization,
    setOriginalPrompt,
    resetState
  } = useRAGAgentStore();
  
  const [sessionId] = useState(() => crypto.randomUUID());
  const { disconnect } = useRAGSSE(sessionId);
  
  // RAG optimization mutation
  const optimizeMutation = useMutation({
    mutationFn: async ({ sessionId, prompt, mode }: { sessionId: string, prompt: string, mode: string }) => {
      const response = await fetch('/api/v2/ai/agent/optimize/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          session_id: sessionId,
          original: prompt,
          mode: mode === 'standard' ? 'fast' : mode.replace('rag-', ''),
          budget: {
            tokens_in: 2000,
            tokens_out: 800,
            max_credits: mode === 'rag-deep' ? 5 : mode === 'rag-fast' ? 3 : 1
          }
        })
      });
      
      if (!response.ok) {
        throw new Error('Optimization failed');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      // Handle non-streaming response
      if (!data.streaming) {
        useRAGAgentStore.getState().handleSSEEvent({
          type: 'agent.done',
          data: data
        });
      }
    }
  });
  
  const handleOptimize = () => {
    if (!originalPrompt.trim()) return;
    
    startOptimization(sessionId, originalPrompt);
    optimizeMutation.mutate({ sessionId, prompt: originalPrompt, mode });
  };
  
  const handleCopyResult = () => {
    if (optimizedPrompt) {
      navigator.clipboard.writeText(optimizedPrompt);
    }
  };
  
  const handleReset = () => {
    resetState();
    disconnect();
  };

  return (
    <div className="temple-background min-h-screen p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-fg flex items-center justify-center gap-3">
            <Brain className="h-8 w-8 text-accent" />
            RAG Agent Optimization
          </h1>
          <p className="text-fg/70">
            Enhance your prompts with AI-powered knowledge retrieval and contextual analysis
          </p>
        </div>

        {/* Mode Selection */}
        <RAGModeToggle />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Input & Controls */}
          <div className="space-y-4">
            <Card variant="temple" padding="lg">
              <h3 className="text-lg font-semibold text-fg mb-4">Original Prompt</h3>
              <textarea
                value={originalPrompt}
                onChange={(e) => setOriginalPrompt(e.target.value)}
                placeholder="Enter your prompt to optimize..."
                className="w-full h-32 p-3 border border-border rounded-lg bg-card text-fg placeholder:text-fg/50 focus:outline-none focus:ring-2 focus:ring-accent resize-none"
                disabled={isOptimizing}
              />
              
              <div className="flex gap-3 mt-4">
                <Button 
                  onClick={handleOptimize}
                  disabled={!originalPrompt.trim() || isOptimizing}
                  className="flex-1"
                >
                  {isOptimizing ? (
                    <>
                      <Sparkles className="h-4 w-4 mr-2 animate-spin" />
                      Optimizing...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" />
                      Optimize with {mode.toUpperCase()}
                    </>
                  )}
                </Button>
                
                {(optimizedPrompt || isOptimizing) && (
                  <Button variant="outline" onClick={handleReset}>
                    Reset
                  </Button>
                )}
              </div>
            </Card>
            
            <BudgetTracker />
            <AgentProgressTracker />
          </div>

          {/* Right Column - Results & Analysis */}
          <div className="space-y-4">
            {/* Optimized Result */}
            {(optimizedPrompt || streamingTokens) && (
              <Card variant="temple" padding="lg">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-fg">Optimized Prompt</h3>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={handleCopyResult}>
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="outline">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                <div className="p-3 border border-border rounded-lg bg-card/50 min-h-32">
                  <pre className="text-fg text-sm leading-relaxed whitespace-pre-wrap">
                    {optimizedPrompt || streamingTokens}
                    {streamingTokens && !optimizedPrompt && (
                      <span className="animate-pulse">|</span>
                    )}
                  </pre>
                </div>
              </Card>
            )}
            
            <Tabs defaultValue="citations" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="citations">Citations</TabsTrigger>
                <TabsTrigger value="analysis">Analysis</TabsTrigger>
              </TabsList>
              
              <TabsContent value="citations">
                <CitationsPanel />
              </TabsContent>
              
              <TabsContent value="analysis">
                <DiffSummary />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};