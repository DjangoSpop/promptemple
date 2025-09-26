// 🏛️ RAG Agent API Integration - Sprint 1 Supporting Files
// File: src/lib/api/ragAgent.ts

import { BaseApiClient } from './base';
import type { components } from '../../types/api';

interface RAGOptimizeRequest {
  session_id: string;
  original: string;
  mode?: 'fast' | 'deep';
  context?: {
    intent?: string;
    domain?: string;
  };
  budget?: {
    tokens_in?: number;
    tokens_out?: number;
    max_credits?: number;
  };
}

interface RAGOptimizeResponse {
  optimized: string;
  citations: Citation[];
  diff_summary: string;
  usage: {
    tokens_in: number;
    tokens_out: number;
    credits: number;
  };
  streaming?: boolean;
  session_id: string;
}

interface Citation {
  id: string;
  title: string;
  score: number;
  source?: string;
  snippet?: string;
}

interface RAGStatsResponse {
  index_status: {
    total_documents: number;
    last_updated: string;
    health: 'healthy' | 'degraded' | 'down';
  };
  user_usage: {
    requests_today: number;
    credits_used: number;
    credits_remaining: number;
  };
  system_metrics: {
    avg_response_time_ms: number;
    success_rate: number;
  };
}

export class RAGAgentService extends BaseApiClient {
  
  /**
   * Optimize prompt using RAG agent
   */
  async optimize(request: RAGOptimizeRequest): Promise<RAGOptimizeResponse> {
    return this.request<RAGOptimizeResponse>('/api/v2/ai/agent/optimize/', {
      method: 'POST',
      data: request,
    });
  }

  /**
   * Get RAG agent statistics
   */
  async getStats(): Promise<RAGStatsResponse> {
    return this.request<RAGStatsResponse>('/api/v2/ai/agent/stats/', {
      method: 'GET',
    });
  }

  /**
   * Get user's optimization history
   */
  async getHistory(limit = 20, offset = 0) {
    return this.request('/api/v2/ai/agent/history/', {
      method: 'GET',
      params: { limit, offset },
    });
  }

  /**
   * Export optimization result
   */
  async exportResult(sessionId: string, format: 'json' | 'txt' | 'pdf' = 'json') {
    return this.request(`/api/v2/ai/agent/export/${sessionId}/`, {
      method: 'GET',
      params: { format },
      responseType: format === 'pdf' ? 'blob' : 'json',
    });
  }
}

export const ragAgentService = new RAGAgentService();

// File: src/hooks/useRAGAgent.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ragAgentService } from '@/lib/api/ragAgent';
import { useRAGAgentStore } from '@/components/optimization/RAGAgentInterface';

export const useRAGAgent = () => {
  const queryClient = useQueryClient();
  
  // Get RAG stats
  const statsQuery = useQuery({
    queryKey: ['rag-agent', 'stats'],
    queryFn: () => ragAgentService.getStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  // Optimization mutation
  const optimizeMutation = useMutation({
    mutationFn: ragAgentService.optimize,
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['rag-agent', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['rag-agent', 'stats'] });
    },
  });

  // History query
  const historyQuery = useQuery({
    queryKey: ['rag-agent', 'history'],
    queryFn: () => ragAgentService.getHistory(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: ({ sessionId, format }: { sessionId: string, format?: 'json' | 'txt' | 'pdf' }) =>
      ragAgentService.exportResult(sessionId, format),
  });

  return {
    // Queries
    stats: statsQuery.data,
    isLoadingStats: statsQuery.isLoading,
    statsError: statsQuery.error,

    history: historyQuery.data,
    isLoadingHistory: historyQuery.isLoading,
    historyError: historyQuery.error,

    // Mutations
    optimize: optimizeMutation.mutate,
    isOptimizing: optimizeMutation.isPending,
    optimizeError: optimizeMutation.error,

    export: exportMutation.mutate,
    isExporting: exportMutation.isPending,
    exportError: exportMutation.error,

    // Utils
    refetchStats: statsQuery.refetch,
    refetchHistory: historyQuery.refetch,
  };
};

// File: src/hooks/useSSEConnection.ts
import { useEffect, useRef, useCallback } from 'react';
import { create } from 'zustand';

interface SSEState {
  connections: Map<string, EventSource>;
  connectionStates: Map<string, 'connecting' | 'connected' | 'disconnected' | 'error'>;
  
  connect: (id: string, url: string, token?: string) => void;
  disconnect: (id: string) => void;
  getConnectionState: (id: string) => string;
}

const useSSEStore = create<SSEState>((set, get) => ({
  connections: new Map(),
  connectionStates: new Map(),
  
  connect: (id: string, url: string, token?: string) => {
    const state = get();
    
    // Close existing connection if any
    const existingConnection = state.connections.get(id);
    if (existingConnection) {
      existingConnection.close();
    }
    
    // Build URL with auth if provided
    const finalUrl = token ? `${url}?token=${encodeURIComponent(token)}` : url;
    
    set(state => ({
      connectionStates: new Map(state.connectionStates.set(id, 'connecting'))
    }));
    
    const eventSource = new EventSource(finalUrl);
    
    eventSource.onopen = () => {
      set(state => ({
        connectionStates: new Map(state.connectionStates.set(id, 'connected'))
      }));
    };
    
    eventSource.onerror = () => {
      set(state => ({
        connectionStates: new Map(state.connectionStates.set(id, 'error'))
      }));
    };
    
    set(state => ({
      connections: new Map(state.connections.set(id, eventSource))
    }));
  },
  
  disconnect: (id: string) => {
    const state = get();
    const connection = state.connections.get(id);
    
    if (connection) {
      connection.close();
      set(state => {
        const newConnections = new Map(state.connections);
        const newStates = new Map(state.connectionStates);
        newConnections.delete(id);
        newStates.set(id, 'disconnected');
        
        return {
          connections: newConnections,
          connectionStates: newStates
        };
      });
    }
  },
  
  getConnectionState: (id: string) => {
    return get().connectionStates.get(id) || 'disconnected';
  }
}));

export const useSSEConnection = (
  id: string,
  url: string,
  options: {
    token?: string;
    autoConnect?: boolean;
    onMessage?: (event: MessageEvent) => void;
    onCustomEvent?: (eventType: string, event: MessageEvent) => void;
  } = {}
) => {
  const { connect, disconnect, getConnectionState, connections } = useSSEStore();
  const { token, autoConnect = true, onMessage, onCustomEvent } = options;
  
  const eventSourceRef = useRef<EventSource | null>(null);
  
  const connectSSE = useCallback(() => {
    connect(id, url, token);
  }, [id, url, token, connect]);
  
  const disconnectSSE = useCallback(() => {
    disconnect(id);
  }, [id, disconnect]);
  
  useEffect(() => {
    if (autoConnect) {
      connectSSE();
    }
    
    return () => {
      disconnectSSE();
    };
  }, [autoConnect, connectSSE, disconnectSSE]);
  
  useEffect(() => {
    const eventSource = connections.get(id);
    if (!eventSource) return;
    
    eventSourceRef.current = eventSource;
    
    if (onMessage) {
      eventSource.onmessage = onMessage;
    }
    
    // Custom event listeners
    if (onCustomEvent) {
      const customEvents = [
        'agent.start', 'agent.step', 'agent.token', 
        'agent.citations', 'agent.done', 'agent.error'
      ];
      
      customEvents.forEach(eventType => {
        eventSource.addEventListener(eventType, (event) => {
          onCustomEvent(eventType, event as MessageEvent);
        });
      });
    }
  }, [connections.get(id), onMessage, onCustomEvent, id]);
  
  return {
    connect: connectSSE,
    disconnect: disconnectSSE,
    connectionState: getConnectionState(id),
    isConnected: getConnectionState(id) === 'connected',
    eventSource: eventSourceRef.current,
  };
};

// File: src/pages/optimization/index.tsx
import { NextPage } from 'next';
import { RAGAgentInterface } from '@/components/optimization/RAGAgentInterface';
import { TempleNavbar } from '@/components/TempleNavbar';

const OptimizationPage: NextPage = () => {
  return (
    <div className="min-h-screen bg-bg">
      <TempleNavbar />
      <main>
        <RAGAgentInterface />
      </main>
    </div>
  );
};

export default OptimizationPage;

// File: src/components/ui/progress.tsx
import React from 'react';
import { cn } from '@/lib/utils';

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  className?: string;
}

export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ value, max = 100, className, ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    
    return (
      <div
        ref={ref}
        className={cn(
          "relative h-2 w-full overflow-hidden rounded-full bg-card border border-border",
          className
        )}
        {...props}
      >
        <div
          className="h-full bg-gradient-to-r from-accent/80 to-accent transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  }
);

Progress.displayName = "Progress";

// File: src/components/ui/scroll-area.tsx
import React from 'react';
import { cn } from '@/lib/utils';

interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ children, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative overflow-hidden",
          className
        )}
        {...props}
      >
        <div className="h-full w-full overflow-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-border">
          {children}
        </div>
      </div>
    );
  }
);

ScrollArea.displayName = "ScrollArea";

// File: src/components/ui/badge.tsx  
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground border-border bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };

// File: src/components/ui/tabs.tsx
import React from 'react';
import * as TabsPrimitive from '@radix-ui/react-tabs';
import { cn } from '@/lib/utils';

const Tabs = TabsPrimitive.Root;

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-card p-1 text-muted-foreground border border-border",
      className
    )}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-accent data-[state=active]:text-accent-foreground data-[state=active]:shadow-sm",
      className
    )}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      className
    )}
    {...props}
  />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };