import React, { useState, useEffect } from 'react';
import { useAuth } from '@/providers/AuthProvider';
import { apiClient } from '@/lib/api-client';
import { TemplateDetail, TemplateList } from '@/lib/types';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Star, 
  Eye, 
  Copy,
  Brain,
  Zap,
  Target,
  Award,
  Clock,
  Download,
  Share,
  Calendar,
  Sparkles,
  BookOpen,
  Wand2,
  ChevronRight,
  ChevronDown,
  Activity,
  Globe,
  Heart,
  Settings,
  AlertCircle,
  CheckCircle,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface TemplateAnalytics {
  usage_stats: {
    total_uses: number;
    unique_users: number;
    completion_rate: number;
    average_rating: number;
    trend: 'up' | 'down' | 'stable';
  };
  performance_metrics: {
    response_time: number;
    success_rate: number;
    user_satisfaction: number;
  };
  ai_insights: {
    complexity_score: number;
    readability_score: number;
    effectiveness_rating: number;
    suggestions: string[];
  };
  usage_patterns: {
    peak_hours: number[];
    popular_fields: string[];
    user_demographics: any;
  };
}

interface EnhancedTemplateAnalyticsProps {
  templateId?: string;
  showOverview?: boolean;
}

export default function EnhancedTemplateAnalytics({ templateId, showOverview = true }: EnhancedTemplateAnalyticsProps) {
  const { user } = useAuth();
  const [template, setTemplate] = useState<TemplateDetail | null>(null);
  const [analytics, setAnalytics] = useState<TemplateAnalytics | null>(null);
  const [myTemplates, setMyTemplates] = useState<TemplateList[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [activeSection, setActiveSection] = useState<'overview' | 'performance' | 'insights' | 'management'>('overview');
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState(false);

  useEffect(() => {
    if (templateId) {
      loadTemplateAnalytics();
    } else if (showOverview) {
      loadOverviewData();
    }
  }, [templateId, selectedTimeRange]);

  const loadTemplateAnalytics = async () => {
    if (!templateId) return;
    
    setIsLoading(true);
    try {
      // Load template details
      const templateData = await apiClient.getTemplate(templateId);
      setTemplate(templateData);

      // Load analytics (mock data for now - replace with actual API calls)
      const analyticsData: TemplateAnalytics = {
        usage_stats: {
          total_uses: templateData.usage_count || 0,
          unique_users: Math.floor((templateData.usage_count || 0) * 0.7),
          completion_rate: templateData.completion_rate || 0.85,
          average_rating: templateData.average_rating || 0,
          trend: templateData.usage_count > 50 ? 'up' : 'stable'
        },
        performance_metrics: {
          response_time: 1.2,
          success_rate: 0.94,
          user_satisfaction: 0.87
        },
        ai_insights: {
          complexity_score: 0.75,
          readability_score: 0.82,
          effectiveness_rating: 0.89,
          suggestions: [
            'Consider adding more specific examples in field descriptions',
            'The template could benefit from clearer variable naming',
            'Adding validation patterns would improve user experience'
          ]
        },
        usage_patterns: {
          peak_hours: [9, 10, 14, 15, 16],
          popular_fields: templateData.fields?.slice(0, 3).map(f => f.label) || [],
          user_demographics: {}
        }
      };
      
      setAnalytics(analyticsData);

      // Track analytics view
      try {
        await apiClient.trackEvent({
          event_type: 'template_analytics_viewed',
          data: {
            template_id: templateId,
            time_range: selectedTimeRange,
          },
        });
      } catch (analyticsError) {
        console.warn('Analytics tracking failed:', analyticsError);
      }
    } catch (error) {
      console.error('Failed to load template analytics:', error);
      setError('Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadOverviewData = async () => {
    setIsLoading(true);
    try {
      // Load user's templates for overview
      const templatesResponse = await apiClient.getTemplates({
        author: user?.id,
        page: 1,
        ordering: '-created_at'
      });
      setMyTemplates(templatesResponse.results || []);
    } catch (error) {
      console.error('Failed to load overview data:', error);
      setError('Failed to load overview data');
    } finally {
      setIsLoading(false);
    }
  };

  const runAIAnalysis = async () => {
    if (!templateId || !template) return;
    
    setAiAnalysisLoading(true);
    try {
      // Call AI analysis endpoint
      await apiClient.analyzeTemplateWithAI(templateId);
      
      // Reload analytics to get updated insights
      await loadTemplateAnalytics();
      
      // Track AI analysis usage
      try {
        await apiClient.trackEvent({
          event_type: 'ai_analysis_requested',
          data: {
            template_id: templateId,
            template_title: template.title,
          },
        });
      } catch (analyticsError) {
        console.warn('Analytics tracking failed:', analyticsError);
      }
    } catch (error) {
      console.error('Failed to run AI analysis:', error);
      setError('Failed to run AI analysis');
    } finally {
      setAiAnalysisLoading(false);
    }
  };

  const toggleCardExpansion = (cardId: string) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(cardId)) {
      newExpanded.delete(cardId);
    } else {
      newExpanded.add(cardId);
    }
    setExpandedCards(newExpanded);
  };

  const MetricCard = ({ 
    title, 
    value, 
    subtitle, 
    icon: Icon, 
    trend, 
    color = 'amber-600',
    expandable = false,
    cardId,
    children 
  }: {
    title: string;
    value: string | number;
    subtitle: string;
    icon: any;
    trend?: 'up' | 'down' | 'stable';
    color?: string;
    expandable?: boolean;
    cardId?: string;
    children?: React.ReactNode;
  }) => {
    const isExpanded = cardId ? expandedCards.has(cardId) : false;
    
    return (
      <Card className="bg-white/90 backdrop-blur-sm shadow-xl border border-amber-200 hover:shadow-2xl transition-all duration-300">
        <div 
          className={`p-6 ${expandable ? 'cursor-pointer' : ''}`}
          onClick={expandable && cardId ? () => toggleCardExpansion(cardId) : undefined}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
              <Icon className={`h-6 w-6 text-${color}`} />
            </div>
            <div className="flex items-center space-x-2">
              {trend && (
                <div className={`flex items-center space-x-1 ${
                  trend === 'up' ? 'text-green-600' : 
                  trend === 'down' ? 'text-red-600' : 'text-gray-500'
                }`}>
                  {trend === 'up' && <ArrowUp className="h-4 w-4" />}
                  {trend === 'down' && <ArrowDown className="h-4 w-4" />}
                  {trend === 'stable' && <Minus className="h-4 w-4" />}
                </div>
              )}
              {expandable && cardId && (
                <div className="text-gray-500">
                  {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </div>
              )}
            </div>
          </div>
          
          <div>
            <div className="text-3xl font-bold text-amber-900 mb-1">
              {value}
            </div>
            <div className="text-sm text-gray-600 mb-2">{title}</div>
            <div className="text-xs text-gray-500">{subtitle}</div>
          </div>
        </div>
        
        {expandable && isExpanded && children && (
          <div className="border-t border-amber-200 p-6">
            {children}
          </div>
        )}
      </Card>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-amber-800 font-semibold">Analyzing sacred data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header Section */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center space-x-4 mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-amber-500 to-orange-600 rounded-full flex items-center justify-center shadow-xl">
              <BarChart3 className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-5xl font-bold text-amber-900 mb-2">
                {templateId ? 'Sacred Analytics' : 'Temple Overview'}
              </h1>
              <p className="text-xl text-amber-700">
                {templateId ? 'Deep insights into template performance' : 'Command center for your temple'}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <Card className="bg-white/90 backdrop-blur-sm p-6 mb-8 shadow-xl border border-amber-200">
          <div className="flex space-x-4 mb-6">
            {['overview', 'performance', 'insights', 'management'].map((section) => (
              <Button
                key={section}
                variant={activeSection === section ? 'default' : 'outline'}
                onClick={() => setActiveSection(section as any)}
                className={activeSection === section 
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white' 
                  : 'border-amber-300 hover:border-amber-500 hover:bg-amber-50'
                }
              >
                {section === 'overview' && <Activity className="h-4 w-4 mr-2" />}
                {section === 'performance' && <TrendingUp className="h-4 w-4 mr-2" />}
                {section === 'insights' && <Brain className="h-4 w-4 mr-2" />}
                {section === 'management' && <Settings className="h-4 w-4 mr-2" />}
                {section.charAt(0).toUpperCase() + section.slice(1)}
              </Button>
            ))}
          </div>

          {/* Time Range Selector */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Time Range:</span>
              <div className="flex space-x-2">
                {[
                  { value: '7d', label: '7 Days' },
                  { value: '30d', label: '30 Days' },
                  { value: '90d', label: '90 Days' },
                  { value: '1y', label: '1 Year' }
                ].map(({ value, label }) => (
                  <Button
                    key={value}
                    variant={selectedTimeRange === value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedTimeRange(value as any)}
                    className={selectedTimeRange === value 
                      ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white' 
                      : 'border-amber-300 hover:border-amber-500 hover:bg-amber-50'
                    }
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </div>

            {templateId && template && (
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  onClick={runAIAnalysis}
                  disabled={aiAnalysisLoading}
                  className="border-emerald-300 hover:border-emerald-500 hover:bg-emerald-50"
                >
                  {aiAnalysisLoading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                  ) : (
                    <Brain className="h-4 w-4 mr-2" />
                  )}
                  AI Analysis
                </Button>
                <Button
                  variant="outline"
                  className="border-amber-300 hover:border-amber-500 hover:bg-amber-50"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Data
                </Button>
              </div>
            )}
          </div>
        </Card>

        {/* Overview Section */}
        {activeSection === 'overview' && (
          <div className="space-y-8">
            {templateId && template && analytics ? (
              <>
                {/* Header Stats */}
                <div className="grid md:grid-cols-4 gap-6">
                  <MetricCard
                    title="Total Uses"
                    value={analytics.usage_stats.total_uses.toLocaleString()}
                    subtitle="Lifetime invocations"
                    icon={Eye}
                    trend={analytics.usage_stats.trend}
                    color="amber-600"
                  />
                  <MetricCard
                    title="Unique Users"
                    value={analytics.usage_stats.unique_users.toLocaleString()}
                    subtitle="Active practitioners"
                    icon={Users}
                    color="emerald-600"
                  />
                  <MetricCard
                    title="Completion Rate"
                    value={`${(analytics.usage_stats.completion_rate * 100).toFixed(1)}%`}
                    subtitle="Successful rituals"
                    icon={CheckCircle}
                    trend="up"
                    color="green-600"
                  />
                  <MetricCard
                    title="Average Rating"
                    value={analytics.usage_stats.average_rating.toFixed(1)}
                    subtitle="User satisfaction"
                    icon={Star}
                    color="amber-500"
                  />
                </div>

                {/* Template Info */}
                <Card className="bg-white/90 backdrop-blur-sm shadow-xl border border-amber-200">
                  <div className="p-6">
                    <h2 className="text-2xl font-bold text-amber-900 mb-4 flex items-center">
                      <BookOpen className="h-6 w-6 mr-3 text-amber-600" />
                      Template Overview
                    </h2>
                    
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <h3 className="text-xl font-semibold text-amber-900 mb-2">{template.title}</h3>
                        <p className="text-gray-600 mb-4">{template.description}</p>
                        
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Category:</span>
                            <span className="text-sm font-medium">{template.category.name}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Fields:</span>
                            <span className="text-sm font-medium">{template.fields.length} dynamic fields</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Created:</span>
                            <span className="text-sm font-medium">
                              {new Date(template.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Version:</span>
                            <span className="text-sm font-medium">{template.version}</span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium text-amber-900 mb-3">Tags</h4>
                        <div className="flex flex-wrap gap-2 mb-4">
                          {template.tags && Array.isArray(template.tags) && template.tags.map((tag: string, index: number) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-amber-100 text-amber-800 rounded border border-amber-200 text-xs"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>

                        <h4 className="font-medium text-amber-900 mb-3">Popular Fields</h4>
                        <div className="space-y-2">
                          {analytics.usage_patterns.popular_fields.map((field, index) => (
                            <div key={index} className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">{field}</span>
                              <div className="w-16 h-2 bg-amber-200 rounded">
                                <div 
                                  className="h-full bg-amber-500 rounded"
                                  style={{ width: `${100 - index * 20}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              </>
            ) : (
              /* Overview for all templates */
              <div className="space-y-6">
                <Card className="bg-white/90 backdrop-blur-sm shadow-xl border border-amber-200">
                  <div className="p-6">
                    <h2 className="text-2xl font-bold text-amber-900 mb-6 flex items-center">
                      <Wand2 className="h-6 w-6 mr-3 text-amber-600" />
                      Your Sacred Templates
                    </h2>

                    {myTemplates.length === 0 ? (
                      <div className="text-center py-12">
                        <BookOpen className="h-16 w-16 text-amber-500 mx-auto mb-4 opacity-50" />
                        <h3 className="text-lg font-medium text-amber-900 mb-2">No Templates Created</h3>
                        <p className="text-gray-600 mb-4">
                          Start creating templates to see analytics and insights here.
                        </p>
                        <Button className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white">
                          <Wand2 className="h-4 w-4 mr-2" />
                          Create Your First Template
                        </Button>
                      </div>
                    ) : (
                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {myTemplates.slice(0, 6).map((template) => (
                          <Card key={template.id} className="bg-white/90 backdrop-blur-sm p-4 hover:shadow-lg transition-all duration-300 cursor-pointer border border-amber-200">
                            <div className="flex items-start justify-between mb-3">
                              <h3 className="font-semibold text-amber-900">{template.title}</h3>
                              {template.is_featured && (
                                <Award className="h-4 w-4 text-amber-500" />
                              )}
                            </div>
                            
                            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                              {template.description}
                            </p>
                            
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <div className="flex items-center space-x-3">
                                <div className="flex items-center space-x-1">
                                  <Eye className="h-3 w-3" />
                                  <span>{template.usage_count}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                  <Star className="h-3 w-3" />
                                  <span>{template.average_rating.toFixed(1)}</span>
                                </div>
                              </div>
                              <span>{template.field_count} fields</span>
                            </div>
                          </Card>
                        ))}
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            )}
          </div>
        )}

        {/* Performance Section */}
        {activeSection === 'performance' && analytics && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-3 gap-6">
              <MetricCard
                title="Response Time"
                value={`${analytics.performance_metrics.response_time.toFixed(1)}s`}
                subtitle="Average processing time"
                icon={Clock}
                color="emerald-600"
              />
              <MetricCard
                title="Success Rate"
                value={`${(analytics.performance_metrics.success_rate * 100).toFixed(1)}%`}
                subtitle="Successful completions"
                icon={Target}
                trend="up"
                color="green-600"
              />
              <MetricCard
                title="User Satisfaction"
                value={`${(analytics.performance_metrics.user_satisfaction * 100).toFixed(1)}%`}
                subtitle="Positive feedback rate"
                icon={Heart}
                color="red-500"
              />
            </div>
          </div>
        )}

        {/* AI Insights Section */}
        {activeSection === 'insights' && analytics && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-3 gap-6">
              <MetricCard
                title="Complexity Score"
                value={`${(analytics.ai_insights.complexity_score * 100).toFixed(0)}%`}
                subtitle="Template complexity level"
                icon={Brain}
                color="amber-600"
              />
              <MetricCard
                title="Readability Score"
                value={`${(analytics.ai_insights.readability_score * 100).toFixed(0)}%`}
                subtitle="User comprehension rating"
                icon={BookOpen}
                color="emerald-600"
              />
              <MetricCard
                title="Effectiveness"
                value={`${(analytics.ai_insights.effectiveness_rating * 100).toFixed(0)}%`}
                subtitle="AI-assessed performance"
                icon={Target}
                trend="up"
                color="green-600"
              />
            </div>

            {/* AI Suggestions */}
            <Card className="bg-white/90 backdrop-blur-sm shadow-xl border border-amber-200">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-semibold text-amber-900 flex items-center">
                    <Sparkles className="h-5 w-5 mr-2 text-amber-600" />
                    AI Recommendations
                  </h3>
                  <Button
                    onClick={runAIAnalysis}
                    disabled={aiAnalysisLoading}
                    className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
                  >
                    {aiAnalysisLoading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    ) : (
                      <Zap className="h-4 w-4 mr-2" />
                    )}
                    Run New Analysis
                  </Button>
                </div>

                <div className="space-y-4">
                  {analytics.ai_insights.suggestions.map((suggestion, index) => (
                    <div key={index} className="flex items-start space-x-3 p-4 bg-amber-50 rounded-lg border border-amber-200">
                      <div className="w-6 h-6 bg-amber-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-xs font-medium text-amber-800">{index + 1}</span>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-amber-900">{suggestion}</p>
                      </div>
                      <Button size="sm" variant="outline" className="border-amber-300 hover:border-amber-500 hover:bg-amber-50">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Apply
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Management Section */}
        {activeSection === 'management' && (
          <div className="space-y-6">
            <Card className="bg-white/90 backdrop-blur-sm shadow-xl border border-amber-200">
              <div className="p-6">
                <h3 className="text-xl font-semibold text-amber-900 mb-6 flex items-center">
                  <Settings className="h-5 w-5 mr-2 text-amber-600" />
                  Template Management
                </h3>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-amber-900">Quick Actions</h4>
                    <div className="space-y-2">
                      <Button className="w-full justify-start bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white">
                        <Copy className="h-4 w-4 mr-2" />
                        Duplicate Template
                      </Button>
                      <Button variant="outline" className="w-full justify-start border-emerald-300 hover:border-emerald-500 hover:bg-emerald-50">
                        <Share className="h-4 w-4 mr-2" />
                        Share Template
                      </Button>
                      <Button variant="outline" className="w-full justify-start border-amber-300 hover:border-amber-500 hover:bg-amber-50">
                        <Download className="h-4 w-4 mr-2" />
                        Export Template
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium text-amber-900">Settings</h4>
                    <div className="space-y-3">
                      <label className="flex items-center justify-between">
                        <span className="text-sm">Public visibility</span>
                        <input 
                          type="checkbox" 
                          defaultChecked={template?.is_public}
                          className="rounded border-amber-300 text-amber-500 focus:ring-amber-500"
                        />
                      </label>
                      <label className="flex items-center justify-between">
                        <span className="text-sm">Featured template</span>
                        <input 
                          type="checkbox" 
                          defaultChecked={template?.is_featured}
                          className="rounded border-amber-300 text-amber-500 focus:ring-amber-500"
                        />
                      </label>
                      <label className="flex items-center justify-between">
                        <span className="text-sm">Analytics tracking</span>
                        <input 
                          type="checkbox" 
                          defaultChecked={true}
                          className="rounded border-amber-300 text-amber-500 focus:ring-amber-500"
                        />
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}