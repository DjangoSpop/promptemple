# Prompt Saving Specification Document
## Complete Integration Guide for Frontend, GraphQL, and Backend

**Version:** 1.0  
**Date:** February 2026  
**Status:** Production Ready  
**Author:** API Integration Team  

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Frontend Implementation](#frontend-implementation)
4. [GraphQL Integration](#graphql-integration)
5. [Backend Storage & Database](#backend-storage--database)
6. [API Endpoints](#api-endpoints)
7. [Integration Workflow](#integration-workflow)
8. [Error Handling & Validation](#error-handling--validation)
9. [Performance Considerations](#performance-considerations)
10. [Security & Authentication](#security--authentication)

---

## Executive Summary

This specification defines the complete prompt saving system enabling users to:
- **Save** prompts for future reuse
- **Organize** prompts with categories and tags
- **Track** usage metrics and favorites
- **Share** prompts with other users (optional)
- **Iterate** on saved prompts with version control

### Key Features
- **Persistent Storage** - User prompts stored in SQLite/PostgreSQL
- **Real-time Metadata** - Use count, last accessed, creation date tracking
- **Flexible Organization** - Categories, tags, descriptions, favorites
- **Version Control** - Track prompt iterations and modifications
- **Full-text Search** - Find prompts by title, content, or tags
- **GraphQL & REST APIs** - Multiple consumption methods

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│               Frontend Application (React)               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  - Save Prompt UI Component                      │   │
│  │  - Prompt Management Dashboard                   │   │
│  │  - Search & Filter Interface                     │   │
│  │  - Favorites & Organization UI                   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   REST API          GraphQL API      WebSocket
   (HTTP Post)    (Mutations/Queries)  (Real-time)
        │                 │                 │
┌───────▼─────────────────▼─────────────────▼───────┐
│         Django Backend (my_prmpt_bakend)           │
│ ┌─────────────────────────────────────────────┐   │
│ │  Views & GraphQL Resolvers                  │   │
│ │  - SavedPromptViewSet                       │   │
│ │  - PromptHistoryViewSet                     │   │
│ │  - PromptIterationViewSet                   │   │
│ │  - GraphQL Mutations & Queries              │   │
│ └─────────────────────────────────────────────┘   │
│ ┌─────────────────────────────────────────────┐   │
│ │  Business Logic & Services                  │   │
│ │  - Prompt Management Service                │   │
│ │  - Search & Indexing Service                │   │
│ │  - Analytics Service                        │   │
│ └─────────────────────────────────────────────┘   │
│ ┌─────────────────────────────────────────────┐   │
│ │  Data Models                                │   │
│ │  - SavedPrompt                              │   │
│ │  - PromptHistory                            │   │
│ │  - PromptIteration                          │   │
│ │  - PromptLibrary                            │   │
│ └─────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
   ┌─────────────┐      ┌──────────────┐
   │  SQLite/    │      │  Cache Layer │
   │  PostgreSQL │      │  (Redis)     │
   │   Database  │      │  Optional    │
   └─────────────┘      └──────────────┘
```

---

## Frontend Implementation

### 1. Components Architecture

#### SavePromptModal Component
```typescript
// Location: src/components/SavePromptModal.tsx

interface SavePromptModalProps {
  isOpen: boolean;
  prompt: string;
  onClose: () => void;
  onSuccess: (savedPrompt: SavedPrompt) => void;
}

interface SavedPrompt {
  id: string;
  title: string;
  content: string;
  description?: string;
  category: string;
  tags: string[];
  useCount: number;
  isFavorite: boolean;
  createdAt: string;
  updatedAt: string;
}
```

#### Key UI Elements
- **Title Input** - Max 200 characters
- **Content Display** - Read-only prompt display
- **Description Field** - Optional notes
- **Category Selector** - Dropdown with predefined categories
  - Writing
  - Coding
  - Analysis
  - Brainstorming
  - Business
  - Custom
- **Tags Input** - Multi-select with autocomplete
- **Success Toast** - Confirmation message

### 2. State Management

```typescript
// Using Redux or Context API
interface PromptSavingState {
  savedPrompts: SavedPrompt[];
  selectedCategory: string;
  searchQuery: string;
  isLoading: boolean;
  error: string | null;
  favorites: string[]; // Array of favorite prompt IDs
}

// Actions
- savingPrompt: (prompt: SavedPromptInput) => void
- loadPrompts: () => void
- deletePrompt: (id: string) => void
- toggleFavorite: (id: string) => void
- searchPrompts: (query: string) => void
```

### 3. API Client Methods

```typescript
// Location: src/api/promptClient.ts

class PromptClient {
  
  // Save a new prompt
  async savePrompt(input: SavePromptInput): Promise<SavedPrompt> {
    const response = await fetch('/api/v2/history/saved-prompts/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(input)
    });
    return response.json();
  }

  // Retrieve all saved prompts for current user
  async getSavedPrompts(
    page?: number,
    category?: string,
    tags?: string[]
  ): Promise<PaginatedResponse<SavedPrompt>> {
    const params = new URLSearchParams();
    if (page) params.append('page', page.toString());
    if (category) params.append('category', category);
    if (tags?.length) params.append('tags', tags.join(','));

    const response = await fetch(
      `/api/v2/history/saved-prompts/?${params}`,
      { headers: { 'Authorization': `Bearer ${authToken}` } }
    );
    return response.json();
  }

  // Update saved prompt
  async updatePrompt(
    id: string,
    updates: Partial<SavePromptInput>
  ): Promise<SavedPrompt> {
    const response = await fetch(
      `/api/v2/history/saved-prompts/${id}/`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(updates)
      }
    );
    return response.json();
  }

  // Delete saved prompt (soft delete)
  async deletePrompt(id: string): Promise<void> {
    await fetch(`/api/v2/history/saved-prompts/${id}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
  }

  // Toggle favorite status
  async toggleFavorite(id: string): Promise<SavedPrompt> {
    const response = await fetch(
      `/api/v2/history/saved-prompts/${id}/toggle-favorite/`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authToken}` }
      }
    );
    return response.json();
  }

  // Record prompt usage
  async recordUsage(id: string): Promise<void> {
    await fetch(
      `/api/v2/history/saved-prompts/${id}/use/`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authToken}` }
      }
    );
  }

  // Search prompts
  async searchPrompts(query: string): Promise<SavedPrompt[]> {
    const response = await fetch(
      `/api/v2/history/saved-prompts/search/?q=${encodeURIComponent(query)}`,
      { headers: { 'Authorization': `Bearer ${authToken}` } }
    );
    return response.json();
  }
}
```

### 4. React Hook for Prompt Management

```typescript
// Location: src/hooks/useSavedPrompts.ts

function useSavedPrompts() {
  const [prompts, setPrompts] = useState<SavedPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const client = new PromptClient();

  // Load prompts on mount
  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async (category?: string) => {
    try {
      setIsLoading(true);
      const data = await client.getSavedPrompts(1, category);
      setPrompts(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const savePrompt = async (input: SavePromptInput) => {
    try {
      const saved = await client.savePrompt(input);
      setPrompts([saved, ...prompts]);
      return saved;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const updatePrompt = async (id: string, updates: Partial<SavePromptInput>) => {
    try {
      const updated = await client.updatePrompt(id, updates);
      setPrompts(prompts.map(p => p.id === id ? updated : p));
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  return {
    prompts,
    isLoading,
    error,
    loadPrompts,
    savePrompt,
    updatePrompt
  };
}
```

---

## GraphQL Integration

### 1. GraphQL Schema Definitions

#### Types
```graphql
# Location: schema.py

type SavedPromptType {
  id: ID!
  user: UserType!
  title: String!
  content: String!
  description: String
  category: String
  tags: [String!]!
  useCount: Int!
  lastUsedAt: DateTime
  isFavorite: Boolean!
  isPublic: Boolean!
  metadata: JSONString!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type PromptHistoryType {
  id: ID!
  user: UserType!
  source: String
  originalPrompt: String!
  optimizedPrompt: String
  modelUsed: String
  tokensInput: Int!
  tokensOutput: Int!
  creditsSpent: Int!
  intentCategory: String
  tags: [String!]!
  meta: JSONString!
  isDeleted: Boolean!
  createdAt: DateTime!
  updatedAt: DateTime!
  iterations: [PromptIterationType!]!
}

type PromptIterationType {
  id: ID!
  parentPrompt: PromptHistoryType!
  iterationNumber: Int!
  versionTag: String
  promptText: String!
  systemMessage: String
  aiResponse: String
  responseModel: String
  interactionType: String!
  changeSummary: String
  parameters: JSONString!
  tags: [String!]!
  metadata: JSONString!
  isActive: Boolean!
  isBookmarked: Boolean!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type SavedPromptListType {
  id: ID!
  title: String!
  content: String!
  description: String
  category: String
  tags: [String!]!
  useCount: Int!
  isFavorite: Boolean!
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Pagination wrapper
type SavedPromptConnection {
  edges: [SavedPromptEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type SavedPromptEdge {
  node: SavedPromptType!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

#### Queries
```graphql
type Query {
  # Retrieve single saved prompt
  savedPrompt(id: ID!): SavedPromptType
  
  # List all saved prompts with filtering and pagination
  savedPrompts(
    first: Int = 10
    after: String
    category: String
    tags: [String!]
    isFavorite: Boolean
    search: String
    orderBy: String = "-updated_at"
  ): SavedPromptConnection!
  
  # Search saved prompts by query
  searchSavedPrompts(
    query: String!
    limit: Int = 20
  ): [SavedPromptType!]!
  
  # Get user's favorite prompts
  favoritePrompts(
    first: Int = 10
    after: String
  ): SavedPromptConnection!
  
  # Get top used prompts
  topUsedPrompts(
    limit: Int = 10
  ): [SavedPromptType!]!
  
  # Retrieve prompt history entries
  promptHistory(
    first: Int = 10
    after: String
    startDate: DateTime
    endDate: DateTime
  ): SavedPromptConnection!
  
  # Get categories available
  promptCategories: [String!]!
  
  # Get popular tags
  popularPromptTags(
    limit: Int = 20
  ): [TagStats!]!
}

type TagStats {
  tag: String!
  count: Int!
}
```

#### Mutations
```graphql
type Mutation {
  # Create/Save a new prompt
  createSavedPrompt(
    input: CreateSavedPromptInput!
  ): CreateSavedPromptPayload!
  
  # Update existing saved prompt
  updateSavedPrompt(
    id: ID!
    input: UpdateSavedPromptInput!
  ): UpdateSavedPromptPayload!
  
  # Delete saved prompt (soft delete)
  deleteSavedPrompt(
    id: ID!
  ): DeleteSavedPromptPayload!
  
  # Toggle favorite status
  toggleFavoriteSavedPrompt(
    id: ID!
  ): ToggleFavoriteSavedPromptPayload!
  
  # Mark prompt as used
  useSavedPrompt(
    id: ID!
  ): UseSavedPromptPayload!
  
  # Bulk operations
  bulkDeletePrompts(
    ids: [ID!]!
  ): BulkDeletePayload!
  
  bulkToggleFavorite(
    ids: [ID!]!
  ): BulkToggleFavoritePayload!
  
  # Batch save multiple prompts
  batchCreatePrompts(
    input: [CreateSavedPromptInput!]!
  ): [CreateSavedPromptPayload!]!
}

# Input types
input CreateSavedPromptInput {
  title: String!
  content: String!
  description: String
  category: String
  tags: [String!]
  metadata: JSONString
}

input UpdateSavedPromptInput {
  title: String
  content: String
  description: String
  category: String
  tags: [String!]
  metadata: JSONString
}

# Payload types
type CreateSavedPromptPayload {
  success: Boolean!
  message: String
  savedPrompt: SavedPromptType
  errors: [FieldError!]
}

type UpdateSavedPromptPayload {
  success: Boolean!
  message: String
  savedPrompt: SavedPromptType
  errors: [FieldError!]
}

type DeleteSavedPromptPayload {
  success: Boolean!
  message: String
  id: ID
}

type ToggleFavoriteSavedPromptPayload {
  success: Boolean!
  message: String
  savedPrompt: SavedPromptType
}

type UseSavedPromptPayload {
  success: Boolean!
  message: String
  savedPrompt: SavedPromptType
}

type BulkDeletePayload {
  success: Boolean!
  deletedCount: Int!
  message: String
}

type BulkToggleFavoritePayload {
  success: Boolean!
  updatedCount: Int!
  message: String
}

type FieldError {
  field: String!
  message: String!
  code: String
}
```

### 2. Frontend GraphQL Queries & Mutations

```typescript
// Location: src/graphql/savedPrompts.ts

import { gql } from '@apollo/client';

// Queries
export const GET_SAVED_PROMPTS = gql`
  query GetSavedPrompts(
    $first: Int!
    $after: String
    $category: String
    $tags: [String!]
    $search: String
  ) {
    savedPrompts(
      first: $first
      after: $after
      category: $category
      tags: $tags
      search: $search
    ) {
      totalCount
      edges {
        node {
          id
          title
          content
          description
          category
          tags
          useCount
          isFavorite
          createdAt
          updatedAt
        }
        cursor
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
    }
  }
`;

export const GET_SAVED_PROMPT = gql`
  query GetSavedPrompt($id: ID!) {
    savedPrompt(id: $id) {
      id
      title
      content
      description
      category
      tags
      useCount
      lastUsedAt
      isFavorite
      isPublic
      metadata
      createdAt
      updatedAt
    }
  }
`;

export const SEARCH_SAVED_PROMPTS = gql`
  query SearchSavedPrompts($query: String!, $limit: Int) {
    searchSavedPrompts(query: $query, limit: $limit) {
      id
      title
      content
      category
      tags
    }
  }
`;

export const GET_FAVORITE_PROMPTS = gql`
  query GetFavoritePrompts($first: Int!, $after: String) {
    favoritePrompts(first: $first, after: $after) {
      totalCount
      edges {
        node {
          id
          title
          content
          category
          tags
          useCount
          createdAt
        }
      }
      pageInfo {
        hasNextPage
      }
    }
  }
`;

// Mutations
export const CREATE_SAVED_PROMPT = gql`
  mutation CreateSavedPrompt($input: CreateSavedPromptInput!) {
    createSavedPrompt(input: $input) {
      success
      message
      savedPrompt {
        id
        title
        content
        description
        category
        tags
        createdAt
      }
      errors {
        field
        message
      }
    }
  }
`;

export const UPDATE_SAVED_PROMPT = gql`
  mutation UpdateSavedPrompt($id: ID!, $input: UpdateSavedPromptInput!) {
    updateSavedPrompt(id: $id, input: $input) {
      success
      message
      savedPrompt {
        id
        title
        content
        category
        tags
        updatedAt
      }
      errors {
        field
        message
      }
    }
  }
`;

export const DELETE_SAVED_PROMPT = gql`
  mutation DeleteSavedPrompt($id: ID!) {
    deleteSavedPrompt(id: $id) {
      success
      message
      id
    }
  }
`;

export const TOGGLE_FAVORITE_PROMPT = gql`
  mutation ToggleFavoritePrompt($id: ID!) {
    toggleFavoriteSavedPrompt(id: $id) {
      success
      message
      savedPrompt {
        id
        isFavorite
      }
    }
  }
`;

export const USE_SAVED_PROMPT = gql`
  mutation UseSavedPrompt($id: ID!) {
    useSavedPrompt(id: $id) {
      success
      message
      savedPrompt {
        id
        useCount
        lastUsedAt
      }
    }
  }
`;

export const BULK_DELETE_PROMPTS = gql`
  mutation BulkDeletePrompts($ids: [ID!]!) {
    bulkDeletePrompts(ids: $ids) {
      success
      deletedCount
      message
    }
  }
`;
```

### 3. GraphQL Resolver Implementation

```python
# Location: apps/prompt_history/schema.py

import graphene
from django.db.models import Q
from .models import SavedPrompt, PromptHistory
from django.utils import timezone

class Query(graphene.ObjectType):
    saved_prompts = graphene.Field(
        SavedPromptConnection,
        first=graphene.Int(default_value=10),
        after=graphene.String(),
        category=graphene.String(),
        tags=graphene.List(graphene.String),
        search=graphene.String(),
        order_by=graphene.String(default_value='-updated_at'),
    )
    
    def resolve_saved_prompts(self, info, first=10, after=None, category=None, 
                            tags=None, search=None, order_by='-updated_at'):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        queryset = SavedPrompt.objects.filter(
            user=user,
            is_deleted=False
        )
        
        # Apply filters
        if category:
            queryset = queryset.filter(category=category)
        
        if tags:
            queryset = queryset.filter(tags__contains=tags)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Apply ordering
        queryset = queryset.order_by(order_by)
        
        # Return paginated results
        return connection_from_list(
            queryset,
            connection_type=SavedPromptConnection,
            first=first,
            after=after,
        )

class CreateSavedPrompt(graphene.Mutation):
    class Arguments:
        input = CreateSavedPromptInput(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    saved_prompt = graphene.Field(SavedPromptType)
    errors = graphene.List(FieldErrorType)
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            return CreateSavedPrompt(
                success=False,
                message="Authentication required",
                errors=[{"field": "auth", "message": "User not authenticated"}]
            )
        
        try:
            saved_prompt = SavedPrompt.objects.create(
                user=user,
                title=input.title,
                content=input.content,
                description=input.description or "",
                category=input.category or "",
                tags=input.tags or [],
                metadata=input.metadata or {}
            )
            
            return CreateSavedPrompt(
                success=True,
                message="Prompt saved successfully",
                saved_prompt=saved_prompt
            )
        except Exception as e:
            return CreateSavedPrompt(
                success=False,
                message=str(e),
                errors=[{"field": "general", "message": str(e)}]
            )

class ToggleFavoriteSavedPrompt(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    saved_prompt = graphene.Field(SavedPromptType)
    
    def mutate(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            return ToggleFavoriteSavedPrompt(
                success=False,
                message="Authentication required"
            )
        
        try:
            saved_prompt = SavedPrompt.objects.get(
                id=id,
                user=user,
                is_deleted=False
            )
            saved_prompt.toggle_favorite()
            
            return ToggleFavoriteSavedPrompt(
                success=True,
                message=f"Prompt {'added to' if saved_prompt.is_favorite else 'removed from'} favorites",
                saved_prompt=saved_prompt
            )
        except SavedPrompt.DoesNotExist:
            return ToggleFavoriteSavedPrompt(
                success=False,
                message="Prompt not found"
            )

class Mutation(graphene.ObjectType):
    create_saved_prompt = CreateSavedPrompt.Field()
    update_saved_prompt = UpdateSavedPrompt.Field()
    delete_saved_prompt = DeleteSavedPrompt.Field()
    toggle_favorite_saved_prompt = ToggleFavoriteSavedPrompt.Field()
    use_saved_prompt = UseSavedPrompt.Field()
```

---

## Backend Storage & Database

### 1. Database Models

#### SavedPrompt Model
```python
# Location: apps/prompt_history/models.py

class SavedPrompt(models.Model):
    """
    User-saved plain prompts for reuse and management.
    Lightweight model for storing frequently-used prompt templates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ownership
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_prompts"
    )
    
    # Content
    title = models.CharField(
        max_length=200,
        help_text="Display title for the saved prompt"
    )
    content = models.TextField(
        help_text="The actual prompt text content"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description or notes about this prompt"
    )
    
    # Organization
    category = models.CharField(
        max_length=100,
        blank=True,
        choices=[
            ('writing', 'Writing & Content'),
            ('coding', 'Programming & Technical'),
            ('analysis', 'Analysis & Research'),
            ('brainstorming', 'Brainstorming'),
            ('business', 'Business & Professional'),
            ('creative', 'Creative & Artistic'),
            ('educational', 'Educational'),
            ('other', 'Other'),
        ],
        db_index=True,
        help_text="Category for organizing prompts"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for searchability and filtering"
    )
    
    # Usage tracking
    use_count = models.IntegerField(
        default=0,
        help_text="Number of times this prompt has been used"
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this prompt was used"
    )
    
    # User preferences
    is_favorite = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this prompt is marked as favorite"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this prompt is publicly visible to other users"
    )
    
    # Flexible metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional flexible metadata (variables, settings, etc.)"
    )
    
    # Status
    is_deleted = models.BooleanField(
        default=False,
        db_index=True
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saved_prompts"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['is_public', 'is_deleted']),
            models.Index(fields=['use_count']),
        ]

    def soft_delete(self):
        """Soft delete the saved prompt"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def increment_use_count(self):
        """Increment usage counter and update last_used_at"""
        self.use_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['use_count', 'last_used_at'])

    def toggle_favorite(self):
        """Toggle the favorite status"""
        self.is_favorite = not self.is_favorite
        self.save(update_fields=['is_favorite'])
        return self.is_favorite
    
    def duplicate(self):
        """Create a duplicate of this prompt"""
        new_prompt = SavedPrompt.objects.create(
            user=self.user,
            title=f"{self.title} (Copy)",
            content=self.content,
            description=self.description,
            category=self.category,
            tags=self.tags.copy(),
            metadata=self.metadata.copy()
        )
        return new_prompt

    def __str__(self):
        return f"SavedPrompt<{self.title}> by {self.user}"
```

#### PromptHistory Model (for tracking usage)
```python
class PromptHistory(models.Model):
    """
    Tracks all prompt interactions and optimizations.
    Links saved prompts to their usage history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prompt_histories"
    )
    
    # Source tracking
    source = models.CharField(max_length=50, blank=True)  # 'saved_prompt', 'manual', etc.
    saved_prompt = models.ForeignKey(
        SavedPrompt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history_entries",
        help_text="Link to original saved prompt"
    )
    
    # Content
    original_prompt = models.TextField()
    optimized_prompt = models.TextField(blank=True)
    
    # AI Model info
    model_used = models.CharField(max_length=100, blank=True)
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    credits_spent = models.IntegerField(default=0)
    
    # Classification
    intent_category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    
    # Status
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "prompt_history"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["intent_category"]),
            models.Index(fields=["is_deleted"]),
            models.Index(fields=["saved_prompt"]),
        ]

    def __str__(self):
        return f"PromptHistory<{self.id}> by {self.user}"
```

### 2. Database Migrations

```bash
# Generate migration
python manage.py makemigrations prompt_history

# Apply migration
python manage.py migrate prompt_history
```

### 3. Database Indexes Strategy

#### Index Optimization
```python
# User's saved prompts by date
Index(fields=['user', 'created_at']) 

# Category browsing
Index(fields=['user', 'category'])

# Favorites viewing
Index(fields=['user', 'is_favorite'])

# Public prompts discovery
Index(fields=['is_public', 'is_deleted'])

# Most used prompts
Index(fields=['use_count'])

# Soft delete queries
Index(fields=['is_deleted'])
```

#### Query Optimization Tips
- Always filter by `user` to ensure data isolation
- Use `select_related()` for foreign keys
- Use `prefetch_related()` for reverse relationships
- Cache frequently accessed categories/tags
- Use database full-text search for content

---

## API Endpoints

### 1. REST API Endpoints

#### SavedPrompt Endpoints
```
POST   /api/v2/history/saved-prompts/
       Create a new saved prompt
       Request: { title, content, description?, category?, tags?, metadata? }
       Response: SavedPrompt object

GET    /api/v2/history/saved-prompts/
       List user's saved prompts with filtering
       Query params: page, category, tags, search, ordering
       Response: Paginated SavedPrompt list

GET    /api/v2/history/saved-prompts/{id}/
       Retrieve specific saved prompt
       Response: SavedPrompt object

PATCH  /api/v2/history/saved-prompts/{id}/
       Partially update saved prompt
       Request: Partial SavedPrompt fields
       Response: Updated SavedPrompt object

PUT    /api/v2/history/saved-prompts/{id}/
       Fully update saved prompt
       Request: Complete SavedPrompt fields
       Response: Updated SavedPrompt object

DELETE /api/v2/history/saved-prompts/{id}/
       Soft delete saved prompt (soft delete)
       Response: 204 No Content

POST   /api/v2/history/saved-prompts/{id}/toggle-favorite/
       Toggle favorite status
       Response: { isFavorite: boolean }

POST   /api/v2/history/saved-prompts/{id}/use/
       Record prompt usage
       Response: { useCount: int, lastUsedAt: datetime }

POST   /api/v2/history/saved-prompts/{id}/duplicate/
       Create a copy of the prompt
       Response: New SavedPrompt object

GET    /api/v2/history/saved-prompts/search/
       Search prompts by query
       Query params: q (search query), limit
       Response: [SavedPrompt]

GET    /api/v2/history/saved-prompts/stats/
       Get user's prompt statistics
       Response: { totalCount, favoriteCount, categoryBreakdown, topTags }
```

### 2. Request/Response Examples

#### Create Saved Prompt
```bash
POST /api/v2/history/saved-prompts/

Request Body:
{
  "title": "Email Marketing Template",
  "content": "Write a compelling email marketing campaign for a tech startup...",
  "description": "Reusable template for marketing emails",
  "category": "business",
  "tags": ["email", "marketing", "template"],
  "metadata": {
    "targetAudience": "tech-savvy",
    "tone": "professional",
    "language": "english"
  }
}

Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user": "user-id",
  "title": "Email Marketing Template",
  "content": "Write a compelling email marketing campaign for a tech startup...",
  "description": "Reusable template for marketing emails",
  "category": "business",
  "tags": ["email", "marketing", "template"],
  "useCount": 0,
  "lastUsedAt": null,
  "isFavorite": false,
  "isPublic": false,
  "metadata": { ... },
  "createdAt": "2026-02-10T10:00:00Z",
  "updatedAt": "2026-02-10T10:00:00Z"
}
```

#### List Saved Prompts
```bash
GET /api/v2/history/saved-prompts/?category=business&page=1

Response (200 OK):
{
  "count": 15,
  "next": "http://api/v2/history/saved-prompts/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Email Marketing Template",
      "category": "business",
      "tags": ["email", "marketing"],
      "useCount": 3,
      "isFavorite": true,
      "createdAt": "2026-02-10T10:00:00Z",
      "updatedAt": "2026-02-10T10:15:00Z"
    },
    ...
  ]
}
```

#### Toggle Favorite
```bash
POST /api/v2/history/saved-prompts/550e8400-e29b-41d4-a716-446655440000/toggle-favorite/

Response (200 OK):
{
  "success": true,
  "message": "Added to favorites",
  "isFavorite": true
}
```

---

## Integration Workflow

### 1. User Saves Prompt (Happy Path)

```
1. User enters prompt text in chat interface
2. User clicks "Save Prompt" button
3. Modal opens with form:
   - Auto-populated: content
   - Manual input: title, description
   - Dropdown: category
   - Multi-select: tags
4. User submits form
5. Frontend sends POST to /api/v2/history/saved-prompts/
6. Backend validates input:
   - Title: required, max 200 chars
   - Content: required
   - Category: optional, must be valid
   - Tags: optional, must be array of strings
7. Backend creates SavedPrompt record
8. Frontend displays success toast
9. Toast includes option to:
   - View saved prompts
   - Save another
   - Close
```

### 2. User Retrieves Saved Prompt

```
1. User navigates to "Saved Prompts" section
2. Frontend loads component with:
   - Category filter dropdown
   - Tag filter multi-select
   - Search input
   - Saved prompts list
3. Frontend sends GET to /api/v2/history/saved-prompts/
4. Backend returns paginated results:
   - First 10 prompts
   - Ordered by most recently updated
5. User can:
   - Click prompt to use it
   - Toggle favorite (star icon)
   - Edit (if owned)
   - Delete (if owned)
   - Duplicate
6. Using prompt triggers POST to /use/ endpoint
   - Increments use_count
   - Updates last_used_at
   - Backend records PromptHistory entry
```

### 3. Search & Discovery Flow

```
1. User types in search box
2. Frontend debounces input (300ms)
3. Frontend sends GET to /api/v2/history/saved-prompts/search/?q=...
4. Backend performs full-text search on:
   - title (weighted higher)
   - content
   - description
   - tags
5. Returns matching prompts (limit 20)
6. Frontend displays results in real-time
7. User clicks result to use/view
```

### 4. Administration & Maintenance

```
Django Admin Interface:
1. Access /admin/prompt_history/savedprompt/
2. List view:
   - Columns: title, category, user, use_count, is_favorite, created_at
   - Filters: category, is_favorite, is_public, date range
   - Search: title, content
   - Actions: soft_delete, toggle_public, export_csv
3. Detail view:
   - Edit any field
   - View history/changes
   - Quick stats (use_count, favorites,last_used)
   - Related entries (history, duplicates)
```

---

## Error Handling & Validation

### 1. Frontend Validation

```typescript
// Input validation before API call
const validateSavePromptInput = (input: SavePromptInput): ValidationError[] => {
  const errors: ValidationError[] = [];

  if (!input.title || input.title.trim().length === 0) {
    errors.push({
      field: 'title',
      message: 'Title is required'
    });
  }

  if (input.title && input.title.length > 200) {
    errors.push({
      field: 'title',
      message: 'Title must be less than 200 characters'
    });
  }

  if (!input.content || input.content.trim().length === 0) {
    errors.push({
      field: 'content',
      message: 'Content/prompt is required'
    });
  }

  if (input.category && !VALID_CATEGORIES.includes(input.category)) {
    errors.push({
      field: 'category',
      message: 'Invalid category selected'
    });
  }

  if (input.tags && input.tags.length > 20) {
    errors.push({
      field: 'tags',
      message: 'Maximum 20 tags allowed'
    });
  }

  return errors;
};
```

### 2. Backend Validation (Django)

```python
# apps/prompt_history/serializers.py
from rest_framework import serializers

class SavedPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedPrompt
        fields = ['id', 'title', 'content', 'description', 'category', 
                  'tags', 'use_count', 'is_favorite', 'created_at', 'updated_at']
        read_only_fields = ['id', 'use_count', 'created_at', 'updated_at']

    def validate_title(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Title cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError("Title max 200 characters")
        return value

    def validate_content(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Content cannot be empty")
        return value

    def validate_tags(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("Maximum 20 tags allowed")
        return [tag.lower().strip() for tag in value if tag.strip()]
```

### 3. Error Response Format

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [
    {
      "field": "title",
      "message": "This field is required",
      "code": "required"
    },
    {
      "field": "tags",
      "message": "Maximum 20 tags allowed",
      "code": "max_length"
    }
  ]
}
```

### 4. Error Codes Reference

| Code | Status | Description |
|------|--------|-------------|
| `required` | 400 | Required field missing |
| `invalid` | 400 | Invalid value format |
| `max_length` | 400 | Value exceeds max length |
| `not_found` | 404 | Resource not found |
| `permission_denied` | 403 | User lacks permission |
| `not_authenticated` | 401 | User not authenticated |
| `duplicate` | 409 | Resource already exists |
| `rate_limit` | 429 | Rate limit exceeded |
| `server_error` | 500 | Internal server error |

---

## Performance Considerations

### 1. Query Optimization

```python
# Bad: N+1 query problem
saved_prompts = SavedPrompt.objects.filter(user=user)
for prompt in saved_prompts:
    print(prompt.user.username)  # Additional query per prompt

# Good: Use select_related
saved_prompts = SavedPrompt.objects.select_related('user').filter(user=user)

# Good: Use prefetch_related for reverse relationships
saved_prompts = SavedPrompt.objects.prefetch_related(
    'history_entries'
).filter(user=user)
```

### 2. Pagination Strategy

```python
# Always use pagination for list endpoints
class SavedPromptViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination  # 10 results per page
    
    def get_queryset(self):
        return SavedPrompt.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('user').order_by('-updated_at')
```

### 3. Caching Strategy

```python
# Cache frequently accessed data
from django.views.decorators.cache import cache_page

class SavedPromptViewSet(viewsets.ModelViewSet):
    @cache_page(60 * 15)  # 15 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

# Cache user's categories
def get_user_categories(user):
    cache_key = f"user_{user.id}_categories"
    categories = cache.get(cache_key)
    if not categories:
        categories = SavedPrompt.objects.filter(
            user=user,
            is_deleted=False
        ).values_list('category', flat=True).distinct()
        cache.set(cache_key, list(categories), 60 * 60)
    return categories
```

### 4. Database Performance

```python
# Create covering indexes for common queries
class SavedPrompt(models.Model):
    class Meta:
        indexes = [
            # Most common user queries
            models.Index(
                fields=['user', 'is_deleted', '-updated_at'],
                name='user_prompts_idx'
            ),
            # Category browsing
            models.Index(
                fields=['user', 'category', 'is_deleted'],
                name='user_category_idx'
            ),
            # Favorite queries
            models.Index(
                fields=['user', 'is_favorite', '-updated_at'],
                name='user_favorites_idx'
            ),
            # Full-text search preparation
            models.Index(
                fields=['content'],
                name='content_search_idx'
            ),
        ]
```

### 5. Frontend Performance

```typescript
// Implement React virtualization for large lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={prompts.length}
  itemSize={100}
  width="100%"
>
  {({ index, style }) => (
    <PromptItem
      style={style}
      prompt={prompts[index]}
    />
  )}
</FixedSizeList>

// Debounce search requests
const debouncedSearch = useCallback(
  debounce((query: string) => {
    searchPrompts(query);
  }, 300),
  []
);

// Use React.memo to prevent unnecessary re-renders
const PromptItem = React.memo(({ prompt }) => (
  <div>{prompt.title}</div>
));
```

---

## Security & Authentication

### 1. Authentication Requirements

```python
# All endpoints require authenticated user
class SavedPromptViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Always filter by current user
        return SavedPrompt.objects.filter(user=self.request.user)
```

### 2. Authorization Checks

```python
# Ensure user can only access their own prompts
def get_object(self):
    obj = SavedPrompt.objects.get(id=self.kwargs['pk'])
    
    # Check if user owns the prompt
    if obj.user != self.request.user:
        raise PermissionDenied("You don't have permission for this prompt")
    
    return obj
```

### 3. Input Sanitization

```python
# Sanitize HTML in content
from bleach import clean

class SavedPromptSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        # Optionally sanitize HTML
        content = validated_data.get('content', '')
        validated_data['content'] = clean(
            content,
            tags=[],  # Strip all HTML tags
            strip=True
        )
        return SavedPrompt.objects.create(**validated_data)
```

### 4. Rate Limiting

```python
# Limit API requests per user
from rest_framework.throttling import UserRateThrottle

class SavePromptThrottle(UserRateThrottle):
    scope = 'save_prompt'
    THROTTLE_RATES = {
        'save_prompt': '100/hour'
    }

class SavedPromptViewSet(viewsets.ModelViewSet):
    throttle_classes = [SavePromptThrottle]
```

### 5. CORS Configuration

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://yourdomain.com",
]

CORS_ALLOW_CREDENTIALS = True
```

---

## Implementation Checklist

### Phase 1: Backend Setup
- [ ] Create SavedPrompt model
- [ ] Create migrations
- [ ] Create serializers
- [ ] Create viewsets and API endpoints
- [ ] Implement GraphQL schema
- [ ] Add validation and error handling
- [ ] Write unit tests

### Phase 2: Frontend Components
- [ ] Create SavePromptModal component
- [ ] Create SavedPromptsPage component
- [ ] Implement usePrompts hook
- [ ] Create PromptClient API helper
- [ ] Implement search/filter UI
- [ ] Add category/tag management

### Phase 3: GraphQL Integration
- [ ] Implement GraphQL queries
- [ ] Implement GraphQL mutations
- [ ] Create frontend GraphQL hooks
- [ ] Test GraphQL end-to-end

### Phase 4: Testing & Documentation
- [ ] Unit tests backend
- [ ] Integration tests
- [ ] E2E tests frontend
- [ ] API documentation
- [ ] User guide documentation

### Phase 5: Deployment
- [ ] Database migration on production
- [ ] API deployment
- [ ] Frontend deployment
- [ ] Monitor performance
- [ ] User feedback & iteration

---

## Appendix: Sample Data

### Sample SavedPrompt JSON
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user": "user-uuid",
  "title": "Technical Blog Post Generator",
  "content": "Generate a comprehensive technical blog post about [TOPIC]. Include: 1) Introduction with context, 2) Main concepts explained clearly, 3) Code examples where relevant, 4) Common pitfalls, 5) Best practices, 6) Conclusion with resources.",
  "description": "Template for generating in-depth technical articles on various programming topics",
  "category": "writing",
  "tags": ["blog", "technical", "writing", "tutorial"],
  "useCount": 7,
  "lastUsedAt": "2026-02-10T15:30:00Z",
  "isFavorite": true,
  "isPublic": false,
  "metadata": {
    "targetAudience": "intermediate-developers",
    "avgLength": "1500-2000 words",
    "tone": "technical-friendly",
    "language": "english"
  },
  "createdAt": "2026-01-15T10:00:00Z",
  "updatedAt": "2026-02-10T15:30:00Z"
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 10, 2026 | Initial specification document created |

---

**Document End**

For questions or clarifications, please contact the API Integration Team.
