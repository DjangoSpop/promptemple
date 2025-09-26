import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/providers/AuthProvider';
import { apiClient } from '@/lib/api-client';
import { TemplateDetail, PromptField } from '@/lib/types';
import { 
  Star, 
  Copy, 
  Eye, 
  Heart, 
  Share, 
  Download,
  Sparkles,
  BookOpen,
  Users,
  Award,
  Play,
  Check,
  AlertCircle,
  Wand2,
  Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface TemplateDetailViewProps {
  templateId: string;
}

interface FieldValue {
  [key: string]: string;
}

export default function EnhancedTemplateDetailView({ templateId }: TemplateDetailViewProps) {
  const { user } = useAuth();
  const router = useRouter();
  const [template, setTemplate] = useState<TemplateDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fieldValues, setFieldValues] = useState<FieldValue>({});
  const [renderedTemplate, setRenderedTemplate] = useState<string>('');
  const [copySuccess, setCopySuccess] = useState<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [activeField, setActiveField] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (templateId) {
      loadTemplate();
    }
  }, [templateId]);

  useEffect(() => {
    if (template) {
      renderTemplate();
    }
  }, [fieldValues, template]);

  const loadTemplate = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.getTemplate(templateId);
      setTemplate(data);
      
      // Initialize field values with defaults
      const initialValues: FieldValue = {};
      data.fields.forEach((field: PromptField) => {
        initialValues[field.label] = field.default_value || '';
      });
      setFieldValues(initialValues);

      // Track template view
      try {
        await apiClient.trackEvent({
          event_type: 'template_viewed',
          data: {
            template_id: templateId,
            template_title: data.title,
          },
        });
      } catch (analyticsError) {
        console.warn('Analytics tracking failed:', analyticsError);
      }
    } catch (error) {
      console.error('Failed to load template:', error);
      setError('Failed to load template');
    } finally {
      setIsLoading(false);
    }
  };

  const renderTemplate = () => {
    if (!template) return;
    
    let rendered = template.template_content;
    
    // Replace template variables with field values
    Object.entries(fieldValues).forEach(([key, value]) => {
      const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
      rendered = rendered.replace(regex, value || `{{${key}}}`);
    });
    
    setRenderedTemplate(rendered);
  };

  const highlightVariables = (content: string) => {
    return content.replace(
      /{{([^}]+)}}/g,
      '<span class="variable-highlight bg-gradient-to-r from-amber-200 to-orange-300 px-2 py-1 rounded-md font-medium text-amber-900 border border-amber-400 shadow-sm animate-pulse">{{$1}}</span>'
    );
  };

  const copyToClipboard = async (text: string, type: string = 'template') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(type);
      setIsAnimating(true);
      
      // Track copy event
      try {
        await apiClient.trackEvent({
          event_type: 'template_copied',
          data: {
            template_id: templateId,
            copy_type: type,
          },
        });
      } catch (analyticsError) {
        console.warn('Analytics tracking failed:', analyticsError);
      }

      setTimeout(() => {
        setCopySuccess(null);
        setIsAnimating(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const handleFieldChange = (fieldLabel: string, value: string) => {
    setFieldValues(prev => ({
      ...prev,
      [fieldLabel]: value
    }));
  };

  const handleUseTemplate = async () => {
    try {
      await apiClient.startTemplateUsage(templateId);
      
      // Track template usage
      try {
        await apiClient.trackEvent({
          event_type: 'template_used',
          data: {
            template_id: templateId,
            field_values: fieldValues,
          },
        });
      } catch (analyticsError) {
        console.warn('Analytics tracking failed:', analyticsError);
      }
    } catch (error) {
      console.error('Failed to start template usage:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-amber-800 font-semibold">Loading sacred wisdom...</p>
        </div>
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error || 'Template not found'}</AlertDescription>
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
              <BookOpen className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-5xl font-bold text-amber-900 mb-2">
                Sacred Template
              </h1>
              <p className="text-xl text-amber-700">
                Forge your wisdom with ancient power
              </p>
            </div>
          </div>
        </div>

        {/* Template Header */}
        <Card className="bg-white/90 backdrop-blur-sm p-8 mb-8 shadow-xl border border-amber-200">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between space-y-6 lg:space-y-0">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-4">
                <h1 className="text-4xl font-bold text-amber-900">
                  {template.title}
                </h1>
                {template.is_featured && (
                  <div className="bg-gradient-to-r from-amber-500 to-orange-500 rounded-full p-2 shadow-lg">
                    <Award className="h-6 w-6 text-white" />
                  </div>
                )}
              </div>
              
              <p className="text-lg text-gray-600 mb-6">
                {template.description}
              </p>

              <div className="flex flex-wrap items-center gap-4 mb-6">
                <div className="flex items-center space-x-2">
                  <Star className="h-5 w-5 text-amber-500 fill-current" />
                  <span className="font-medium text-amber-900">
                    {template.average_rating.toFixed(1)} ({template.usage_count} uses)
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-emerald-600" />
                  <span className="text-gray-600">
                    By {template.author.username}
                  </span>
                </div>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full border border-emerald-200">
                  {template.category.name}
                </span>
              </div>

              <div className="flex flex-wrap gap-2 mb-6">
                {template.tags && Array.isArray(template.tags) && template.tags.map((tag: string, index: number) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-amber-100 text-amber-800 rounded border border-amber-200 text-sm"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex flex-col space-y-3 lg:w-64">
              <Button 
                className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white w-full shadow-lg"
                onClick={handleUseTemplate}
              >
                <Play className="h-4 w-4 mr-2" />
                Invoke Template
              </Button>
              
              <div className="grid grid-cols-2 gap-2">
                <Button 
                  variant="outline" 
                  className="border-amber-300 hover:border-amber-500 hover:bg-amber-50"
                  onClick={() => copyToClipboard(template.template_content, 'raw')}
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <Button 
                  variant="outline"
                  className="border-emerald-300 hover:border-emerald-500 hover:bg-emerald-50"
                >
                  <Heart className="h-4 w-4" />
                </Button>
              </div>
              
              <Button 
                variant="outline"
                className="border-red-300 hover:border-red-500 hover:bg-red-50"
              >
                <Share className="h-4 w-4 mr-2" />
                Share Template
              </Button>
            </div>
          </div>
        </Card>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Template Fields */}
          <Card className="bg-white/90 backdrop-blur-sm shadow-xl border border-amber-200">
            <div className="p-6 border-b border-amber-200">
              <h2 className="text-2xl font-bold text-amber-900 flex items-center">
                <Wand2 className="h-6 w-6 mr-3 text-amber-600" />
                Sacred Fields
              </h2>
              <p className="text-gray-600 mt-2">
                Fill in the fields to customize your template
              </p>
            </div>

            <div className="p-6 space-y-6">
              {template.fields.length === 0 ? (
                <div className="text-center py-8">
                  <Sparkles className="h-12 w-12 text-amber-500 mx-auto mb-4 opacity-50" />
                  <p className="text-gray-600">
                    This template has no dynamic fields
                  </p>
                </div>
              ) : (
                template.fields.map((field: PromptField, index: number) => (
                  <div 
                    key={field.id} 
                    className={`space-y-2 p-4 rounded-lg border transition-all duration-300 ${
                      activeField === field.label 
                        ? 'border-amber-400 bg-amber-50 shadow-lg transform scale-105' 
                        : 'border-gray-200 hover:border-amber-300'
                    }`}
                    onFocus={() => setActiveField(field.label)}
                    onBlur={() => setActiveField(null)}
                  >
                    <label className="block font-medium text-amber-900 flex items-center">
                      <Zap className="h-4 w-4 mr-2 text-amber-600" />
                      {field.label}
                      {field.is_required && (
                        <span className="text-red-500 ml-1">*</span>
                      )}
                    </label>
                    
                    {field.help_text && (
                      <p className="text-sm text-gray-600">
                        {field.help_text}
                      </p>
                    )}

                    {field.field_type === 'textarea' ? (
                      <textarea
                        className="w-full p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 bg-white resize-none transition-all duration-300"
                        rows={4}
                        placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}...`}
                        value={fieldValues[field.label] || ''}
                        onChange={(e) => handleFieldChange(field.label, e.target.value)}
                      />
                    ) : field.field_type === 'number' ? (
                      <input
                        type="number"
                        className="w-full p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 bg-white transition-all duration-300"
                        placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}...`}
                        value={fieldValues[field.label] || ''}
                        onChange={(e) => handleFieldChange(field.label, e.target.value)}
                      />
                    ) : (
                      <input
                        type="text"
                        className="w-full p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 bg-white transition-all duration-300"
                        placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}...`}
                        value={fieldValues[field.label] || ''}
                        onChange={(e) => handleFieldChange(field.label, e.target.value)}
                      />
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Right Column - Template Preview */}
          <Card className="bg-white/90 backdrop-blur-sm shadow-xl border border-amber-200">
            <div className="p-6 border-b border-amber-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-amber-900 flex items-center">
                  <Eye className="h-6 w-6 mr-3 text-emerald-600" />
                  Live Preview
                </h2>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(renderedTemplate, 'rendered')}
                    className={`transition-all duration-300 ${
                      copySuccess === 'rendered' 
                        ? 'border-green-500 bg-green-50' 
                        : 'border-amber-300 hover:border-amber-500 hover:bg-amber-50'
                    }`}
                  >
                    {copySuccess === 'rendered' ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>

            <div className="p-6">
              <div className="space-y-4">
                {/* Raw Template with Highlighted Variables */}
                <div>
                  <h3 className="font-medium text-amber-900 mb-2 flex items-center">
                    <BookOpen className="h-4 w-4 mr-2" />
                    Template Structure
                  </h3>
                  <div 
                    className="p-4 bg-gray-50 rounded-lg border border-amber-200 font-mono text-sm"
                    dangerouslySetInnerHTML={{ 
                      __html: highlightVariables(template.template_content) 
                    }}
                  />
                </div>

                {/* Rendered Output */}
                <div>
                  <h3 className="font-medium text-amber-900 mb-2 flex items-center">
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generated Output
                  </h3>
                  <div className="relative">
                    <textarea
                      ref={textareaRef}
                      className="w-full p-4 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-300 rounded-lg font-mono text-sm text-amber-900 resize-none transition-all duration-300 focus:border-amber-500 focus:shadow-lg"
                      rows={12}
                      value={renderedTemplate}
                      readOnly
                    />
                    
                    {/* Copy Success Animation */}
                    {copySuccess && isAnimating && (
                      <div className="absolute inset-0 bg-green-500/20 rounded-lg flex items-center justify-center animate-ping">
                        <div className="bg-green-500 text-white px-4 py-2 rounded-lg font-medium">
                          Copied to clipboard!
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Template Actions */}
        <Card className="bg-white/90 backdrop-blur-sm p-6 mt-8 shadow-xl border border-amber-200">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div>
              <h3 className="text-xl font-bold text-amber-900">
                Ready to use your template?
              </h3>
              <p className="text-gray-600">
                Copy the generated content or download it for later use.
              </p>
            </div>
            
            <div className="flex space-x-3">
              <Button
                className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-lg"
                onClick={() => copyToClipboard(renderedTemplate, 'final')}
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy Final Result
              </Button>
              
              <Button
                variant="outline"
                className="border-emerald-300 hover:border-emerald-500 hover:bg-emerald-50"
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <style jsx>{`
        .variable-highlight {
          display: inline-block;
          animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
          from {
            box-shadow: 0 0 5px rgba(251, 191, 36, 0.5);
          }
          to {
            box-shadow: 0 0 15px rgba(251, 191, 36, 0.8);
          }
        }
      `}</style>
    </div>
  );
}