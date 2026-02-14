# Prompt Saving Quick Reference Guide
## Implementation Checklist & Code Snippets

---

## Quick Start - Frontend Integration

### 1. Install Dependencies
```bash
npm install @apollo/client graphql
npm install react-hook-form  # For form management
npm install react-toastify   # For notifications
```

### 2. Create SavePromptModal Component
```typescript
// src/components/SavePromptModal.tsx
import React, { useState } from 'react';
import { useMutation } from '@apollo/client';
import { CREATE_SAVED_PROMPT } from '../graphql/savedPrompts';
import { toast } from 'react-toastify';

interface SavePromptModalProps {
  isOpen: boolean;
  prompt: string;
  onClose: () => void;
  onSuccess?: (savedPrompt: any) => void;
}

export const SavePromptModal: React.FC<SavePromptModalProps> = ({
  isOpen,
  prompt,
  onClose,
  onSuccess
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('other');
  const [tags, setTags] = useState<string[]>([]);

  const [createPrompt, { loading }] = useMutation(CREATE_SAVED_PROMPT);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      toast.error('Title is required');
      return;
    }

    try {
      const { data } = await createPrompt({
        variables: {
          input: {
            title,
            content: prompt,
            description,
            category,
            tags
          }
        }
      });

      if (data?.createSavedPrompt?.success) {
        toast.success('Prompt saved successfully!');
        onSuccess?.(data.createSavedPrompt.savedPrompt);
        onClose();
      } else {
        toast.error(data?.createSavedPrompt?.message || 'Failed to save prompt');
      }
    } catch (error: any) {
      toast.error(error.message || 'Error saving prompt');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Save Prompt</h2>
        <form onSubmit={handleSave}>
          <div className="form-group">
            <label>Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
              placeholder="Give your prompt a descriptive name"
              required
            />
          </div>

          <div className="form-group">
            <label>Category</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="writing">Writing & Content</option>
              <option value="coding">Programming & Technical</option>
              <option value="analysis">Analysis & Research</option>
              <option value="brainstorming">Brainstorming</option>
              <option value="business">Business & Professional</option>
              <option value="creative">Creative & Artistic</option>
              <option value="educational">Educational</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional notes about this prompt"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label>Tags</label>
            <input
              type="text"
              placeholder="Enter tags separated by commas"
              onChange={(e) => setTags(e.target.value.split(',').map(t => t.trim()))}
            />
          </div>

          <div className="prompt-preview">
            <strong>Prompt Content:</strong>
            <p>{prompt}</p>
          </div>

          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={loading}>
              {loading ? 'Saving...' : 'Save Prompt'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

### 3. Use SavePromptModal in Your App
```typescript
// src/pages/ChatPage.tsx
import { SavePromptModal } from '../components/SavePromptModal';

export const ChatPage = () => {
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [showSaveModal, setShowSaveModal] = useState(false);

  return (
    <div>
      <textarea
        value={currentPrompt}
        onChange={(e) => setCurrentPrompt(e.target.value)}
        placeholder="Enter your prompt..."
      />
      
      <button onClick={() => setShowSaveModal(true)}>
        Save This Prompt
      </button>

      <SavePromptModal
        isOpen={showSaveModal}
        prompt={currentPrompt}
        onClose={() => setShowSaveModal(false)}
        onSuccess={(saved) => {
          console.log('Saved prompt:', saved);
          setCurrentPrompt('');
        }}
      />
    </div>
  );
};
```

---

## Backend Integration Steps

### 1. Create Database Model
```python
# apps/prompt_history/models.py
from django.db import models
import uuid

class SavedPrompt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True, default='other')
    tags = models.JSONField(default=list, blank=True)
    use_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_favorite = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saved_prompts'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'is_favorite']),
        ]

    def increment_use_count(self):
        self.use_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['use_count', 'last_used_at'])
```

### 2. Create Serializer
```python
# apps/prompt_history/serializers.py
from rest_framework import serializers
from .models import SavedPrompt

class SavedPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedPrompt
        fields = ['id', 'title', 'content', 'description', 'category', 
                  'tags', 'use_count', 'is_favorite', 'created_at', 'updated_at']
        read_only_fields = ['id', 'use_count', 'created_at', 'updated_at']
```

### 3. Create ViewSet
```python
# apps/prompt_history/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SavedPrompt
from .serializers import SavedPromptSerializer

class SavedPromptViewSet(viewsets.ModelViewSet):
    serializer_class = SavedPromptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedPrompt.objects.filter(user=self.request.user, is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        prompt = self.get_object()
        prompt.is_favorite = not prompt.is_favorite
        prompt.save()
        return Response({'success': True, 'is_favorite': prompt.is_favorite})

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        prompt = self.get_object()
        prompt.increment_use_count()
        return Response(self.get_serializer(prompt).data)
```

### 4. Register URL
```python
# apps/prompt_history/urls.py
from rest_framework.routers import DefaultRouter
from .views import SavedPromptViewSet

router = DefaultRouter()
router.register(r'saved-prompts', SavedPromptViewSet, basename='saved-prompts')

urlpatterns = router.urls
```

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## GraphQL Integration

### 1. Add GraphQL Type
```python
# apps/prompt_history/schema.py
import graphene
from graphene_django import DjangoObjectType
from .models import SavedPrompt

class SavedPromptType(DjangoObjectType):
    class Meta:
        model = SavedPrompt
        fields = '__all__'

class Query(graphene.ObjectType):
    saved_prompts = graphene.List(SavedPromptType)
    
    def resolve_saved_prompts(self, info):
        if info.context.user.is_authenticated:
            return SavedPrompt.objects.filter(
                user=info.context.user,
                is_deleted=False
            )
        return SavedPrompt.objects.none()

class CreateSavedPrompt(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        category = graphene.String()
        tags = graphene.List(graphene.String)

    saved_prompt = graphene.Field(SavedPromptType)
    success = graphene.Boolean()

    def mutate(self, info, title, content, category=None, tags=None):
        if not info.context.user.is_authenticated:
            return CreateSavedPrompt(success=False, saved_prompt=None)

        prompt = SavedPrompt.objects.create(
            user=info.context.user,
            title=title,
            content=content,
            category=category or 'other',
            tags=tags or []
        )
        return CreateSavedPrompt(success=True, saved_prompt=prompt)

class Mutation(graphene.ObjectType):
    create_saved_prompt = CreateSavedPrompt.Field()
```

---

## API Usage Examples

### REST API Examples

#### Save a Prompt
```bash
curl -X POST http://localhost:8000/api/v2/history/saved-prompts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Email Template",
    "content": "Write a professional email about...",
    "category": "business",
    "tags": ["email", "professional"]
  }'
```

#### List Saved Prompts
```bash
curl http://localhost:8000/api/v2/history/saved-prompts/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Mark as Favorite
```bash
curl -X POST http://localhost:8000/api/v2/history/saved-prompts/{id}/toggle-favorite/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Record Usage
```bash
curl -X POST http://localhost:8000/api/v2/history/saved-prompts/{id}/use/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### GraphQL Examples

#### Create Using GraphQL
```graphql
mutation {
  createSavedPrompt(
    input: {
      title: "Marketing Email"
      content: "Write a compelling email..."
      category: "business"
      tags: ["email", "marketing"]
    }
  ) {
    success
    savedPrompt {
      id
      title
      createdAt
    }
  }
}
```

#### Query Saved Prompts
```graphql
query {
  savedPrompts(first: 10, category: "business") {
    edges {
      node {
        id
        title
        content
        category
        tags
        useCount
        isFavorite
      }
    }
    pageInfo {
      hasNextPage
    }
  }
}
```

---

## Testing Checklist

### Frontend Tests
- [ ] Modal opens when button clicked
- [ ] Title validation works
- [ ] Form submission successful
- [ ] Success toast appears
- [ ] Loading state shows during submission
- [ ] Error handling works
- [ ] Modal closes on success
- [ ] Saved prompt appears in list

### Backend Tests
```python
# tests/test_saved_prompts.py
from django.test import TestCase
from django.contrib.auth.models import User
from apps.prompt_history.models import SavedPrompt

class SavedPromptTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')

    def test_create_saved_prompt(self):
        prompt = SavedPrompt.objects.create(
            user=self.user,
            title='Test Prompt',
            content='Test content'
        )
        self.assertEqual(prompt.title, 'Test Prompt')

    def test_increment_use_count(self):
        prompt = SavedPrompt.objects.create(
            user=self.user,
            title='Test',
            content='Test'
        )
        prompt.increment_use_count()
        self.assertEqual(prompt.use_count, 1)

    def test_toggle_favorite(self):
        prompt = SavedPrompt.objects.create(
            user=self.user,
            title='Test',
            content='Test'
        )
        prompt.toggle_favorite()
        self.assertTrue(prompt.is_favorite)
```

### API Tests
```python
def test_api_create_saved_prompt(self):
    response = self.client.post(
        '/api/v2/history/saved-prompts/',
        {
            'title': 'Test',
            'content': 'Test content',
            'category': 'coding'
        },
        format='json'
    )
    self.assertEqual(response.status_code, 201)
    self.assertEqual(response.data['title'], 'Test')
```

---

## Common Issues & Solutions

### Issue 1: CORS Errors
```python
# settings.py
INSTALLED_APPS = [
    'corsheaders',
    ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add this
    'django.middleware.common.CommonMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
]
```

### Issue 2: User Not Authenticated
```python
# Ensure token is sent with requests
// Frontend
const response = await fetch('/api/endpoint', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Issue 3: Database Migrations Conflicts
```bash
# Squash migrations if needed
python manage.py squashmigrations prompt_history

# Reset database (development only)
python manage.py migrate prompt_history zero
python manage.py migrate prompt_history
```

### Issue 4: Performance with Large Datasets
```python
# Use select_related and prefetch_related
queryset = SavedPrompt.objects.select_related('user').filter(...)

# Add pagination
from rest_framework.pagination import PageNumberPagination

class SavedPromptViewSet(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination
    paginate_by = 10
```

---

## Next Steps

1. **Copy the specification document** from PROMPT_SAVING_SPECIFICATION.md
2. **Review the architecture** with your team
3. **Implement phase by phase** following the checklist
4. **Test thoroughly** at each stage
5. **Deploy to production** gradually
6. **Monitor and iterate** based on user feedback

---

## Support & Resources

- **Specification:** See PROMPT_SAVING_SPECIFICATION.md
- **API Documentation:** /api/docs/ (Swagger/DRF)
- **GraphQL Sandbox:** /graphql/ (GraphiQL)
- **Admin Dashboard:** /admin/prompt_history/savedprompt/

---

**Last Updated:** February 10, 2026  
**Version:** 1.0
