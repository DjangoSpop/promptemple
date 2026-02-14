# Saved Prompts GraphQL API - Frontend Integration Specification

Complete GraphQL CRUD API for managing user-saved plain prompts. This system enables users to save, organize, and reuse their prompts independently from the iteration/history system.

## 📋 Table of Contents

1. [Overview](#overview)
2. [API Endpoint](#api-endpoint)
3. [Data Model](#data-model)
4. [Queries](#queries)
5. [Mutations](#mutations)
6. [TypeScript Types](#typescript-types)
7. [React Hook Examples](#react-hook-examples)
8. [Integration Workflow](#integration-workflow)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

---

## Overview

The SavedPrompt system provides a simple CRUD interface for managing plain prompts that users want to save for future reuse. Unlike the iteration/history system, saved prompts are:

- **Standalone**: Not tied to optimization history or AI interactions
- **User-owned**: Each user manages their own collection
- **Categorizable**: Organize with categories and tags
- **Shareable**: Option to make prompts public
- **Trackable**: Usage count and last-used timestamps

### Key Features

| Feature | Description |
|---------|-------------|
| **Create** | Save new prompts with title, content, and metadata |
| **Read** | Retrieve prompts with filtering and search |
| **Update** | Modify existing prompts |
| **Delete** | Soft-delete prompts (recoverable) |
| **Favorite** | Toggle favorite status for quick access |
| **Duplicate** | Create copies of existing prompts |
| **Track Usage** | Record when prompts are used |
| **Public Sharing** | Make prompts available to other users |

---

## API Endpoint

```
POST /api/graphql/
```

### Authentication

All requests require JWT authentication:

```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

---

## Data Model

### SavedPrompt Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Auto | Unique identifier |
| `title` | String | ✅ | Display title (max 200 chars) |
| `content` | String | ✅ | The actual prompt text |
| `description` | String | ❌ | Optional notes about the prompt |
| `category` | String | ❌ | Category for organization |
| `tags` | [String] | ❌ | Array of tags for filtering |
| `useCount` | Int | Auto | Number of times used |
| `lastUsedAt` | DateTime | Auto | Last usage timestamp |
| `isFavorite` | Boolean | ❌ | Favorite status (default: false) |
| `isPublic` | Boolean | ❌ | Public visibility (default: false) |
| `metadata` | JSON | ❌ | Additional flexible data |
| `isDeleted` | Boolean | Auto | Soft delete flag |
| `createdAt` | DateTime | Auto | Creation timestamp |
| `updatedAt` | DateTime | Auto | Last update timestamp |

---

## Queries

### 1. Get Single Saved Prompt

Retrieve a specific prompt by ID.

```graphql
query GetSavedPrompt($id: UUID!) {
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
```

**Variables:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 2. Get All Saved Prompts

Retrieve all user's saved prompts with optional filtering.

```graphql
query GetAllSavedPrompts(
  $category: String
  $isFavorite: Boolean
  $limit: Int
  $offset: Int
) {
  allSavedPrompts(
    category: $category
    isFavorite: $isFavorite
    limit: $limit
    offset: $offset
  ) {
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
    createdAt
    updatedAt
  }
}
```

**Variables:**
```json
{
  "category": "coding",
  "isFavorite": true,
  "limit": 20,
  "offset": 0
}
```

---

### 3. Get Favorite Saved Prompts

Retrieve only favorited prompts.

```graphql
query GetFavoriteSavedPrompts($limit: Int) {
  favoriteSavedPrompts(limit: $limit) {
    id
    title
    content
    category
    tags
    useCount
    createdAt
  }
}
```

---

### 4. Search Saved Prompts

Full-text search across title, content, and description.

```graphql
query SearchSavedPrompts(
  $query: String!
  $category: String
  $tags: [String]
  $limit: Int
) {
  searchSavedPrompts(
    query: $query
    category: $category
    tags: $tags
    limit: $limit
  ) {
    id
    title
    content
    description
    category
    tags
    useCount
    isFavorite
    createdAt
  }
}
```

**Variables:**
```json
{
  "query": "write a blog post",
  "category": "writing",
  "tags": ["creative", "marketing"],
  "limit": 10
}
```

---

### 5. Get Public Saved Prompts

Retrieve prompts shared by all users.

```graphql
query GetPublicSavedPrompts($category: String, $limit: Int) {
  publicSavedPrompts(category: $category, limit: $limit) {
    id
    title
    content
    description
    category
    tags
    useCount
    user {
      id
      username
    }
    createdAt
  }
}
```

---

## Mutations

### 1. Create Saved Prompt

Save a new plain prompt.

```graphql
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
      isFavorite
      isPublic
      metadata
      createdAt
    }
  }
}
```

**Variables:**
```json
{
  "input": {
    "title": "Blog Post Writer",
    "content": "Write a compelling blog post about {{topic}} that engages readers and includes actionable insights. The tone should be {{tone}} and target audience is {{audience}}.",
    "description": "A versatile prompt for generating blog content",
    "category": "writing",
    "tags": ["blog", "content", "marketing"],
    "isFavorite": false,
    "isPublic": false,
    "metadata": {
      "variables": ["topic", "tone", "audience"],
      "estimatedTokens": 150
    }
  }
}
```

---

### 2. Update Saved Prompt

Modify an existing prompt.

```graphql
mutation UpdateSavedPrompt($input: UpdateSavedPromptInput!) {
  updateSavedPrompt(input: $input) {
    success
    message
    savedPrompt {
      id
      title
      content
      description
      category
      tags
      isFavorite
      isPublic
      metadata
      updatedAt
    }
  }
}
```

**Variables:**
```json
{
  "input": {
    "promptId": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Updated Blog Post Writer",
    "content": "Updated prompt content...",
    "tags": ["blog", "content", "marketing", "seo"]
  }
}
```

---

### 3. Delete Saved Prompt

Soft-delete a prompt (can be recovered).

```graphql
mutation DeleteSavedPrompt($promptId: UUID!) {
  deleteSavedPrompt(promptId: $promptId) {
    success
    message
  }
}
```

**Variables:**
```json
{
  "promptId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 4. Toggle Favorite

Add or remove prompt from favorites.

```graphql
mutation ToggleFavoriteSavedPrompt($promptId: UUID!) {
  toggleFavoriteSavedPrompt(promptId: $promptId) {
    success
    message
    isFavorite
    savedPrompt {
      id
      title
      isFavorite
    }
  }
}
```

---

### 5. Use Saved Prompt

Record prompt usage (increments counter and updates lastUsedAt).

```graphql
mutation UseSavedPrompt($promptId: UUID!) {
  useSavedPrompt(promptId: $promptId) {
    success
    message
    savedPrompt {
      id
      useCount
      lastUsedAt
    }
  }
}
```

---

### 6. Duplicate Saved Prompt

Create a copy of an existing prompt.

```graphql
mutation DuplicateSavedPrompt($promptId: UUID!, $newTitle: String) {
  duplicateSavedPrompt(promptId: $promptId, newTitle: $newTitle) {
    success
    message
    savedPrompt {
      id
      title
      content
      category
      tags
      createdAt
    }
  }
}
```

**Variables:**
```json
{
  "promptId": "550e8400-e29b-41d4-a716-446655440000",
  "newTitle": "Blog Post Writer v2"
}
```

---

## TypeScript Types

```typescript
// Core Types
interface SavedPrompt {
  id: string;
  title: string;
  content: string;
  description: string;
  category: string;
  tags: string[];
  useCount: number;
  lastUsedAt: string | null;
  isFavorite: boolean;
  isPublic: boolean;
  metadata: Record<string, any>;
  isDeleted: boolean;
  createdAt: string;
  updatedAt: string;
}

// Input Types
interface CreateSavedPromptInput {
  title: string;
  content: string;
  description?: string;
  category?: string;
  tags?: string[];
  isFavorite?: boolean;
  isPublic?: boolean;
  metadata?: Record<string, any>;
}

interface UpdateSavedPromptInput {
  promptId: string;
  title?: string;
  content?: string;
  description?: string;
  category?: string;
  tags?: string[];
  isFavorite?: boolean;
  isPublic?: boolean;
  metadata?: Record<string, any>;
}

// Response Types
interface MutationResponse<T = null> {
  success: boolean;
  message: string;
  savedPrompt?: T extends null ? never : SavedPrompt;
}

interface ToggleFavoriteResponse extends MutationResponse<SavedPrompt> {
  isFavorite: boolean;
}

// Query Variables
interface GetAllSavedPromptsVars {
  category?: string;
  isFavorite?: boolean;
  limit?: number;
  offset?: number;
}

interface SearchSavedPromptsVars {
  query: string;
  category?: string;
  tags?: string[];
  limit?: number;
}
```

---

## React Hook Examples

### useSavedPrompts Hook

```typescript
import { gql, useQuery, useMutation } from '@apollo/client';

// Queries
const GET_ALL_SAVED_PROMPTS = gql`
  query GetAllSavedPrompts($category: String, $limit: Int, $offset: Int) {
    allSavedPrompts(category: $category, limit: $limit, offset: $offset) {
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
  }
`;

const SEARCH_SAVED_PROMPTS = gql`
  query SearchSavedPrompts($query: String!, $category: String, $tags: [String], $limit: Int) {
    searchSavedPrompts(query: $query, category: $category, tags: $tags, limit: $limit) {
      id
      title
      content
      category
      tags
      useCount
      isFavorite
    }
  }
`;

// Mutations
const CREATE_SAVED_PROMPT = gql`
  mutation CreateSavedPrompt($input: CreateSavedPromptInput!) {
    createSavedPrompt(input: $input) {
      success
      message
      savedPrompt {
        id
        title
        content
        category
        tags
        createdAt
      }
    }
  }
`;

const UPDATE_SAVED_PROMPT = gql`
  mutation UpdateSavedPrompt($input: UpdateSavedPromptInput!) {
    updateSavedPrompt(input: $input) {
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
    }
  }
`;

const DELETE_SAVED_PROMPT = gql`
  mutation DeleteSavedPrompt($promptId: UUID!) {
    deleteSavedPrompt(promptId: $promptId) {
      success
      message
    }
  }
`;

const TOGGLE_FAVORITE = gql`
  mutation ToggleFavoriteSavedPrompt($promptId: UUID!) {
    toggleFavoriteSavedPrompt(promptId: $promptId) {
      success
      isFavorite
      savedPrompt {
        id
        isFavorite
      }
    }
  }
`;

const USE_PROMPT = gql`
  mutation UseSavedPrompt($promptId: UUID!) {
    useSavedPrompt(promptId: $promptId) {
      success
      savedPrompt {
        id
        useCount
        lastUsedAt
      }
    }
  }
`;

// Custom Hook
export function useSavedPrompts(options?: { category?: string; limit?: number }) {
  const { data, loading, error, refetch } = useQuery(GET_ALL_SAVED_PROMPTS, {
    variables: {
      category: options?.category,
      limit: options?.limit || 50,
      offset: 0,
    },
  });

  const [createPrompt] = useMutation(CREATE_SAVED_PROMPT, {
    refetchQueries: ['GetAllSavedPrompts'],
  });

  const [updatePrompt] = useMutation(UPDATE_SAVED_PROMPT);

  const [deletePrompt] = useMutation(DELETE_SAVED_PROMPT, {
    refetchQueries: ['GetAllSavedPrompts'],
  });

  const [toggleFavorite] = useMutation(TOGGLE_FAVORITE);

  const [usePrompt] = useMutation(USE_PROMPT);

  return {
    prompts: data?.allSavedPrompts || [],
    loading,
    error,
    refetch,
    createPrompt: async (input: CreateSavedPromptInput) => {
      const result = await createPrompt({ variables: { input } });
      return result.data?.createSavedPrompt;
    },
    updatePrompt: async (input: UpdateSavedPromptInput) => {
      const result = await updatePrompt({ variables: { input } });
      return result.data?.updateSavedPrompt;
    },
    deletePrompt: async (promptId: string) => {
      const result = await deletePrompt({ variables: { promptId } });
      return result.data?.deleteSavedPrompt;
    },
    toggleFavorite: async (promptId: string) => {
      const result = await toggleFavorite({ variables: { promptId } });
      return result.data?.toggleFavoriteSavedPrompt;
    },
    usePrompt: async (promptId: string) => {
      const result = await usePrompt({ variables: { promptId } });
      return result.data?.useSavedPrompt;
    },
  };
}
```

### Usage Example

```tsx
import { useSavedPrompts } from './hooks/useSavedPrompts';

function SavedPromptsPage() {
  const {
    prompts,
    loading,
    error,
    createPrompt,
    deletePrompt,
    toggleFavorite,
    usePrompt,
  } = useSavedPrompts({ category: 'writing' });

  const handleSavePrompt = async () => {
    const result = await createPrompt({
      title: 'My New Prompt',
      content: 'Write something amazing about...',
      category: 'writing',
      tags: ['creative'],
    });
    
    if (result.success) {
      console.log('Saved:', result.savedPrompt);
    }
  };

  const handleUsePrompt = async (promptId: string, content: string) => {
    // Record usage
    await usePrompt(promptId);
    
    // Use the prompt content in your app
    navigator.clipboard.writeText(content);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <button onClick={handleSavePrompt}>Save New Prompt</button>
      
      <ul>
        {prompts.map((prompt) => (
          <li key={prompt.id}>
            <h3>{prompt.title}</h3>
            <p>{prompt.content}</p>
            <span>Used {prompt.useCount} times</span>
            
            <button onClick={() => toggleFavorite(prompt.id)}>
              {prompt.isFavorite ? '★' : '☆'}
            </button>
            
            <button onClick={() => handleUsePrompt(prompt.id, prompt.content)}>
              Use
            </button>
            
            <button onClick={() => deletePrompt(prompt.id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Integration Workflow

### Save Prompt Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User Action: "Save this prompt"                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: Show save dialog                                 │
│  - Title (required)                                         │
│  - Category (optional dropdown)                             │
│  - Tags (optional chips)                                    │
│  - Description (optional)                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Mutation: createSavedPrompt                                │
│  POST /api/graphql/                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Response: success + savedPrompt                            │
│  - Update local cache                                       │
│  - Show success toast                                       │
└─────────────────────────────────────────────────────────────┘
```

### Use Prompt Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User: Clicks "Use" on saved prompt                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Mutation: useSavedPrompt(promptId)                         │
│  - Increments useCount                                      │
│  - Updates lastUsedAt                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: Insert prompt content                            │
│  - Copy to clipboard, OR                                    │
│  - Insert into active input, OR                             │
│  - Pass to AI chat interface                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling

### GraphQL Errors

```typescript
interface GraphQLError {
  message: string;
  locations?: { line: number; column: number }[];
  path?: string[];
  extensions?: {
    code: string;
    exception?: any;
  };
}

// Common error codes
const ERROR_CODES = {
  AUTHENTICATION_REQUIRED: 'Authentication required',
  PROMPT_NOT_FOUND: 'Saved prompt not found',
  VALIDATION_ERROR: 'Error saving prompt:',
} as const;

// Error handling example
const handleGraphQLError = (error: ApolloError) => {
  const message = error.graphQLErrors?.[0]?.message || error.message;
  
  if (message.includes('Authentication required')) {
    // Redirect to login
    router.push('/login');
    return;
  }
  
  if (message.includes('not found')) {
    // Prompt was deleted
    toast.error('This prompt no longer exists');
    refetch();
    return;
  }
  
  // Generic error
  toast.error(message);
};
```

### Mutation Response Handling

```typescript
const handleMutationResponse = <T>(
  response: MutationResponse<T>,
  successMessage?: string
) => {
  if (response.success) {
    if (successMessage) {
      toast.success(successMessage);
    }
    return response;
  } else {
    toast.error(response.message);
    throw new Error(response.message);
  }
};

// Usage
const result = await createPrompt({ title, content });
handleMutationResponse(result, 'Prompt saved!');
```

---

## Best Practices

### 1. Optimistic Updates

```typescript
const [toggleFavorite] = useMutation(TOGGLE_FAVORITE, {
  optimisticResponse: ({ promptId }) => ({
    __typename: 'Mutation',
    toggleFavoriteSavedPrompt: {
      __typename: 'ToggleFavoriteSavedPromptPayload',
      success: true,
      isFavorite: true, // Toggle optimistically
      savedPrompt: {
        __typename: 'SavedPromptType',
        id: promptId,
        isFavorite: true,
      },
    },
  }),
});
```

### 2. Cache Updates

```typescript
const [deletePrompt] = useMutation(DELETE_SAVED_PROMPT, {
  update(cache, { data }) {
    if (data?.deleteSavedPrompt?.success) {
      cache.modify({
        fields: {
          allSavedPrompts(existing = [], { readField }) {
            return existing.filter(
              (ref: any) => readField('id', ref) !== promptId
            );
          },
        },
      });
    }
  },
});
```

### 3. Pagination

```typescript
const { data, fetchMore } = useQuery(GET_ALL_SAVED_PROMPTS, {
  variables: { limit: 20, offset: 0 },
});

const loadMore = () => {
  fetchMore({
    variables: {
      offset: data.allSavedPrompts.length,
    },
    updateQuery: (prev, { fetchMoreResult }) => ({
      allSavedPrompts: [
        ...prev.allSavedPrompts,
        ...fetchMoreResult.allSavedPrompts,
      ],
    }),
  });
};
```

### 4. Search Debouncing

```typescript
import { useDebouncedCallback } from 'use-debounce';

const [searchQuery, setSearchQuery] = useState('');
const { data } = useQuery(SEARCH_SAVED_PROMPTS, {
  variables: { query: searchQuery },
  skip: !searchQuery,
});

const debouncedSearch = useDebouncedCallback(
  (value: string) => setSearchQuery(value),
  300
);
```

---

## Categories Suggestion

For consistent organization, consider these predefined categories:

| Category | Description |
|----------|-------------|
| `coding` | Programming and development |
| `writing` | Content creation, blogs, articles |
| `analysis` | Data analysis, research |
| `creative` | Creative writing, brainstorming |
| `business` | Business documents, emails |
| `academic` | Academic writing, research |
| `marketing` | Marketing copy, ads |
| `translation` | Language translation |
| `chat` | Conversational prompts |
| `other` | Miscellaneous |

---

## Migration from Existing System

If migrating from PromptHistory to SavedPrompt:

```graphql
# Get existing prompts from history
query GetHistoryToMigrate {
  allPromptHistories(limit: 100) {
    id
    originalPrompt
    optimizedPrompt
    intentCategory
    tags
    createdAt
  }
}

# Create saved prompts from history
mutation MigratePrompt($input: CreateSavedPromptInput!) {
  createSavedPrompt(input: $input) {
    success
    savedPrompt { id }
  }
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-08 | Initial SavedPrompt CRUD API |

---

## Support

For issues or questions:
- Check the GraphQL playground at `/api/graphql/`
- Review Django admin at `/admin/prompt_history/savedprompt/`
- Contact the backend team

