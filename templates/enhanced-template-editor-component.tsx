import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/providers/AuthProvider';
import { apiClient } from '@/lib/api-client';
import { TemplateCategory } from '@/lib/types';
import { 
  Save, 
  Plus, 
  Trash2, 
  Eye, 
  EyeOff,
  ArrowLeft,
  Wand2,
  FileText,
  Tag,
  Globe,
  Sparkles,
  Type,
  Hash,
  List,
  CheckSquare,
  AlertCircle,
  Check,
  X,
  Move,
  Settings,
  Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface PromptField {
  id: string;
  label: string;
  field_type: 'text' | 'textarea' | 'number' | 'dropdown' | 'checkbox' | 'radio';
  placeholder?: string;
  help_text?: string;
  is_required: boolean;
  default_value?: string;
  options?: string[];
  order: number;
}

interface EnhancedTemplateEditorProps {
  templateId?: string;
  isEditing?: boolean;
}

export default function EnhancedTemplateEditor({ templateId, isEditing = false }: EnhancedTemplateEditorProps) {
  const router = useRouter();
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [activeTab, setActiveTab] = useState<'content' | 'fields' | 'settings'>('content');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    template_content: '',
    category: null as number | null,
    tags: [] as string[],
    is_public: true,
    is_featured: false,
    version: '1.0'
  });

  const [fields, setFields] = useState<PromptField[]>([]);
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [previewContent, setPreviewContent] = useState('');

  useEffect(() => {
    loadCategories();
    if (isEditing && templateId) {
      loadTemplate();
    }
  }, [templateId, isEditing]);

  useEffect(() => {
    generatePreview();
  }, [formData.template_content, fields]);

  const loadCategories = async () => {
    try {
      const response = await apiClient.getTemplateCategories();
      setCategories(response.results || []);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const loadTemplate = async () => {
    if (!templateId) return;
    
    setIsLoading(true);
    try {
      const template = await apiClient.getTemplate(templateId);
      setFormData({
        title: template.title,
        description: template.description,
        template_content: template.template_content,
        category: template.category.id,
        tags: Array.isArray(template.tags) ? template.tags : [],
        is_public: template.is_public,
        is_featured: template.is_featured,
        version: template.version || '1.0'
      });
      setFields(template.fields || []);
    } catch (error) {
      console.error('Failed to load template:', error);
      setError('Failed to load template');
    } finally {
      setIsLoading(false);
    }
  };

  const generatePreview = () => {
    let preview = formData.template_content;
    
    // Add syntax highlighting for variables
    preview = preview.replace(
      /{{([^}]+)}}/g,
      '<span class="bg-yellow-200 px-1 rounded text-yellow-800">{{$1}}</span>'
    );
    
    setPreviewContent(preview);
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const addField = (type: PromptField['field_type'] = 'text') => {
    const newField: PromptField = {
      id: crypto.randomUUID(),
      label: '',
      field_type: type,
      placeholder: '',
      help_text: '',
      is_required: false,
      default_value: '',
      order: fields.length,
    };
    setFields(prev => [...prev, newField]);
  };

  const updateField = (id: string, field: string, value: any) => {
    setFields(prev => prev.map(f => 
      f.id === id ? { ...f, [field]: value } : f
    ));
  };

  const removeField = (id: string) => {
    setFields(prev => prev.filter(f => f.id !== id));
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag)
    }));
  };

  const insertVariable = (variableName: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = formData.template_content;
    const before = text.substring(0, start);
    const after = text.substring(end);
    const variable = `{{${variableName}}}`;

    handleInputChange('template_content', before + variable + after);
    
    // Reset cursor position
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + variable.length, start + variable.length);
    }, 0);
  };

  const handleSubmit = async () => {
    if (!user) {
      setError('You must be logged in to create templates');
      return;
    }

    if (!formData.title.trim() || !formData.template_content.trim()) {
      setError('Title and template content are required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const fieldsData = fields.map((field, index) => ({
        label: field.label,
        placeholder: field.placeholder || '',
        field_type: field.field_type,
        is_required: field.is_required,
        default_value: field.default_value || '',
        validation_pattern: '',
        help_text: field.help_text || '',
        options: field.options ? JSON.stringify(field.options) : '',
        order: index
      }));

      const templateData = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        template_content: formData.template_content.trim(),
        category: formData.category || 1,
        tags: JSON.stringify(formData.tags),
        is_public: formData.is_public,
        version: formData.version,
        fields_data: fieldsData,
      };

      let result;
      if (isEditing && templateId) {
        result = await apiClient.updateTemplate(templateId, templateData);
        setSuccessMessage('Template updated successfully!');
      } else {
        result = await apiClient.createTemplate(templateData);
        setSuccessMessage('Template created successfully!');
      }
      
      // Track the action
      try {
        await apiClient.trackEvent({
          event_type: isEditing ? 'template_updated' : 'template_created',
          data: {
            template_id: result.id,
            template_title: result.title,
            fields_count: fields.length,
            tags_count: formData.tags.length,
          },
        });
      } catch (analyticsError) {
        console.warn('Analytics tracking failed:', analyticsError);
      }

      // Redirect to the template
      setTimeout(() => {
        router.push(`/templates/${result.id}`);
      }, 1500);

    } catch (error: any) {
      console.error('Failed to save template:', error);
      setError('Failed to save template. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const FieldTypeIcon = ({ type }: { type: PromptField['field_type'] }) => {
    switch (type) {
      case 'text': return <Type className="h-4 w-4" />;
      case 'textarea': return <FileText className="h-4 w-4" />;
      case 'number': return <Hash className="h-4 w-4" />;
      case 'dropdown': return <List className="h-4 w-4" />;
      case 'checkbox': return <CheckSquare className="h-4 w-4" />;
      case 'radio': return <CheckSquare className="h-4 w-4" />;
      default: return <Type className="h-4 w-4" />;
    }
  };

  const TabButton = ({ tab, label, icon: Icon }: { tab: string, label: string, icon: any }) => (
    <button
      type="button"
      onClick={() => setActiveTab(tab as any)}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-300 ${
        activeTab === tab
          ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg'
          : 'text-gray-600 hover:text-amber-600 hover:bg-amber-50'
      }`}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </button>
  );

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You must be logged in to create templates. Please log in and try again.
          </AlertDescription>
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
              <Wand2 className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-5xl font-bold text-amber-900 mb-2">
                {isEditing ? 'The Sacred Forge' : 'The Creation Chamber'}
              </h1>
              <p className="text-xl text-amber-700">
                {isEditing ? 'Refine ancient wisdom' : 'Craft new wisdom for eternity'}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 mb-6">
          <Button 
            variant="outline" 
            onClick={() => router.back()}
            className="border-amber-300 hover:border-amber-500 hover:bg-amber-50"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Return to Archive
          </Button>
          <h2 className="text-2xl font-bold text-amber-900">
            {isEditing ? 'Edit Sacred Template' : 'Forge New Template'}
          </h2>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {successMessage && (
          <Alert className="mb-6 bg-green-50 border-green-200">
            <Check className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              {successMessage}
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-6">
          {/* Tab Navigation */}
          <Card className="bg-white/90 backdrop-blur-sm shadow-xl border border-amber-200">
            <div className="p-6">
              <div className="flex space-x-4 mb-6">
                <TabButton tab="content" label="Content" icon={FileText} />
                <TabButton tab="fields" label="Fields" icon={Wand2} />
                <TabButton tab="settings" label="Settings" icon={Settings} />
              </div>

              {/* Content Tab */}
              {activeTab === 'content' && (
                <div className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-amber-900">
                        Template Title <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        className="w-full p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 bg-white"
                        placeholder="Enter a powerful title..."
                        value={formData.title}
                        onChange={(e) => handleInputChange('title', e.target.value)}
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2 text-amber-900">Category</label>
                      <select
                        className="w-full p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 bg-white"
                        value={formData.category || ''}
                        onChange={(e) => handleInputChange('category', e.target.value ? parseInt(e.target.value) : null)}
                      >
                        <option value="">Select sacred category...</option>
                        {categories.map((category) => (
                          <option key={category.id} value={category.id}>
                            {category.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-amber-900">Description</label>
                    <textarea
                      className="w-full p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 bg-white resize-none"
                      rows={3}
                      placeholder="Describe the power of your template..."
                      value={formData.description}
                      onChange={(e) => handleInputChange('description', e.target.value)}
                    />
                  </div>

                  <div className="grid lg:grid-cols-2 gap-6">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-amber-900">
                          Template Content <span className="text-red-500">*</span>
                        </label>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setShowPreview(!showPreview)}
                          className="border-amber-300 hover:border-amber-500 hover:bg-amber-50"
                        >
                          {showPreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          {showPreview ? 'Hide' : 'Preview'}
                        </Button>
                      </div>
                      
                      <textarea
                        ref={textareaRef}
                        className="w-full p-4 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 bg-white font-mono resize-none"
                        rows={12}
                        placeholder="Enter your template content... Use {{variable_name}} for dynamic fields."
                        value={formData.template_content}
                        onChange={(e) => handleInputChange('template_content', e.target.value)}
                        required
                      />
                      
                      <p className="text-sm text-gray-600 mt-2">
                        Use {"{{variable_name}}"} to create dynamic placeholders. Click field names to insert them.
                      </p>
                    </div>

                    {showPreview && (
                      <div>
                        <label className="block text-sm font-medium mb-2 text-amber-900">Live Preview</label>
                        <div 
                          className="w-full p-4 border border-emerald-300 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 font-mono text-sm min-h-64"
                          dangerouslySetInnerHTML={{ __html: previewContent }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Quick Insert Variables */}
                  {fields.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium mb-2 text-amber-900">
                        Quick Insert Variables
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {fields.map((field) => (
                          <Button
                            key={field.id}
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => insertVariable(field.label)}
                            className="border-amber-300 hover:border-amber-500 hover:bg-amber-50"
                          >
                            <Zap className="h-3 w-3 mr-1" />
                            {field.label}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Fields Tab */}
              {activeTab === 'fields' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-amber-900">Dynamic Fields</h3>
                    <Button
                      type="button"
                      onClick={() => addField('text')}
                      className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Field
                    </Button>
                  </div>

                  {/* Field Type Quick Add */}
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                    {[
                      { type: 'text', label: 'Text', icon: Type },
                      { type: 'textarea', label: 'Textarea', icon: FileText },
                      { type: 'number', label: 'Number', icon: Hash },
                      { type: 'dropdown', label: 'Dropdown', icon: List },
                      { type: 'checkbox', label: 'Checkbox', icon: CheckSquare },
                      { type: 'radio', label: 'Radio', icon: CheckSquare },
                    ].map(({ type, label, icon: Icon }) => (
                      <Button
                        key={type}
                        type="button"
                        variant="outline"
                        onClick={() => addField(type as PromptField['field_type'])}
                        className="flex flex-col items-center p-3 h-auto border-amber-300 hover:border-amber-500 hover:bg-amber-50"
                      >
                        <Icon className="h-4 w-4 mb-1" />
                        <span className="text-xs">{label}</span>
                      </Button>
                    ))}
                  </div>

                  {fields.length === 0 ? (
                    <div className="text-center py-12 border-2 border-dashed border-amber-300 rounded-lg">
                      <Sparkles className="h-12 w-12 text-amber-500 mx-auto mb-4 opacity-50" />
                      <p className="text-gray-600 mb-4">
                        No dynamic fields created yet.
                      </p>
                      <Button
                        type="button"
                        onClick={() => addField('text')}
                        className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Create Your First Field
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {fields.map((field, index) => (
                        <Card key={field.id} className="bg-white/90 backdrop-blur-sm p-4 shadow-lg border border-amber-200">
                          <div className="space-y-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                                  <FieldTypeIcon type={field.field_type} />
                                </div>
                                <span className="font-medium text-amber-900">
                                  Field {index + 1}
                                </span>
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  onClick={() => insertVariable(field.label)}
                                  disabled={!field.label}
                                  className="border-emerald-300 hover:border-emerald-500 hover:bg-emerald-50"
                                >
                                  <Zap className="h-3 w-3 mr-1" />
                                  Insert
                                </Button>
                              </div>
                              
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => removeField(field.id)}
                                className="border-red-300 hover:border-red-500 hover:bg-red-50"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>

                            <div className="grid md:grid-cols-2 gap-4">
                              <div>
                                <label className="block text-sm font-medium mb-1">Label</label>
                                <input
                                  type="text"
                                  className="w-full p-2 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 bg-white"
                                  placeholder="Field label..."
                                  value={field.label}
                                  onChange={(e) => updateField(field.id, 'label', e.target.value)}
                                />
                              </div>

                              <div>
                                <label className="block text-sm font-medium mb-1">Type</label>
                                <select
                                  className="w-full p-2 border border-amber-300 rounded-lg bg-white"
                                  value={field.field_type}
                                  onChange={(e) => updateField(field.id, 'field_type', e.target.value)}
                                >
                                  <option value="text">Text</option>
                                  <option value="textarea">Textarea</option>
                                  <option value="number">Number</option>
                                  <option value="dropdown">Dropdown</option>
                                  <option value="checkbox">Checkbox</option>
                                  <option value="radio">Radio</option>
                                </select>
                              </div>
                            </div>

                            <div className="grid md:grid-cols-2 gap-4">
                              <div>
                                <label className="block text-sm font-medium mb-1">Placeholder</label>
                                <input
                                  type="text"
                                  className="w-full p-2 border border-amber-300 rounded-lg bg-white"
                                  placeholder="Placeholder text..."
                                  value={field.placeholder || ''}
                                  onChange={(e) => updateField(field.id, 'placeholder', e.target.value)}
                                />
                              </div>

                              <div>
                                <label className="block text-sm font-medium mb-1">Help Text</label>
                                <input
                                  type="text"
                                  className="w-full p-2 border border-amber-300 rounded-lg bg-white"
                                  placeholder="Help text..."
                                  value={field.help_text || ''}
                                  onChange={(e) => updateField(field.id, 'help_text', e.target.value)}
                                />
                              </div>
                            </div>

                            <div className="flex items-center space-x-4">
                              <label className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  checked={field.is_required}
                                  onChange={(e) => updateField(field.id, 'is_required', e.target.checked)}
                                  className="rounded border-amber-300 text-amber-500 focus:ring-amber-500"
                                />
                                <span className="text-sm text-amber-900">Required</span>
                              </label>
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Settings Tab */}
              {activeTab === 'settings' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-amber-900">Tags</h3>
                    <div className="flex gap-2 mb-4">
                      <input
                        type="text"
                        className="flex-1 p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 bg-white"
                        placeholder="Add sacred tags..."
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                      />
                      <Button 
                        type="button" 
                        onClick={addTag} 
                        disabled={!tagInput.trim()}
                        className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
                      >
                        <Tag className="h-4 w-4 mr-2" />
                        Add
                      </Button>
                    </div>

                    {formData.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {formData.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-amber-100 text-amber-800 border border-amber-200"
                          >
                            #{tag}
                            <button
                              type="button"
                              onClick={() => removeTag(tag)}
                              className="ml-2 text-amber-600 hover:text-amber-800"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-4 text-amber-900">Visibility</h3>
                      <div className="space-y-3">
                        <label className="flex items-center space-x-3">
                          <input
                            type="checkbox"
                            checked={formData.is_public}
                            onChange={(e) => handleInputChange('is_public', e.target.checked)}
                            className="rounded border-amber-300 text-amber-500 focus:ring-amber-500"
                          />
                          <div className="flex items-center space-x-2">
                            <Globe className="h-4 w-4 text-amber-600" />
                            <span className="text-amber-900">Make template public</span>
                          </div>
                        </label>

                        <label className="flex items-center space-x-3">
                          <input
                            type="checkbox"
                            checked={formData.is_featured}
                            onChange={(e) => handleInputChange('is_featured', e.target.checked)}
                            className="rounded border-amber-300 text-amber-500 focus:ring-amber-500"
                          />
                          <div className="flex items-center space-x-2">
                            <Sparkles className="h-4 w-4 text-amber-600" />
                            <span className="text-amber-900">Feature this template</span>
                          </div>
                        </label>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold mb-4 text-amber-900">Version</h3>
                      <input
                        type="text"
                        className="w-full p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 bg-white"
                        placeholder="1.0"
                        value={formData.version}
                        onChange={(e) => handleInputChange('version', e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Submit Actions */}
          <div className="flex justify-end gap-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => router.back()}
              className="border-amber-300 hover:border-amber-500 hover:bg-amber-50"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit}
              disabled={isLoading}
              className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-lg"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {isEditing ? 'Updating...' : 'Creating...'}
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  {isEditing ? 'Update Template' : 'Create Template'}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}