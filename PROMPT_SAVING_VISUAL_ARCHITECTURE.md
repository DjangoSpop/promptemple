# Prompt Saving - Visual Integration Guide
## Architecture, Data Flow & Component Relationships

---

## 1. System Architecture Diagram

### Complete Stack View

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER BROWSER                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │         Frontend React Application (my_prmpt_frontend)         │   │
│  │                                                               │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  Chat Interface                                     │    │   │
│  │  │  - User enters prompt                               │    │   │
│  │  │  - AI generates response                            │    │   │
│  │  │  - User can save prompt with button                │    │   │
│  │  └──────────────────────┬──────────────────────────────┘    │   │
│  │                         │                                   │   │
│  │  ┌──────────────────────▼──────────────────────────────┐    │   │
│  │  │  SavePromptModal Component                         │    │   │
│  │  │  - Title input (max 200 chars)                     │    │   │
│  │  │  - Description textarea                            │    │   │
│  │  │  - Category dropdown                               │    │   │
│  │  │  - Tags multi-select                               │    │   │
│  │  │  - Preview display                                 │    │   │
│  │  └──────────────────────┬──────────────────────────────┘    │   │
│  │                         │                                   │   │
│  │  ┌──────────────────────▼──────────────────────────────┐    │   │
│  │  │  SavedPromptsPage Component                        │    │   │
│  │  │  - List all saved prompts                          │    │   │
│  │  │  - Filter by category & tags                       │    │   │
│  │  │  - Search functionality                            │    │   │
│  │  │  - Toggle favorite                                 │    │   │
│  │  │  - Edit/Delete actions                             │    │   │
│  │  └──────────────────────┬──────────────────────────────┘    │   │
│  │                         │                                   │   │
│  │  ┌──────────────────────▼──────────────────────────────┐    │   │
│  │  │  API Client & GraphQL Hooks                        │    │   │
│  │  │  - usePrompts()                                    │    │   │
│  │  │  - useSavePrompt()                                 │    │   │
│  │  │  - useSearchPrompts()                              │    │   │
│  │  └──────────────────────┬──────────────────────────────┘    │   │
│  └──────────────────────────┼──────────────────────────────────┘   │
└─────────────────────────────┼─────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
       [REST API]       [GraphQL API]    [WebSocket]
       (HTTP Post)      (Queries/Mutations) (Real-time)
              │               │               │
              └───────────────┼───────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────────┐
│                    DJANGO BACKEND SERVER                          │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │           API Layer (DRF ViewSets & GraphQL)             │    │
│  │                                                          │    │
│  │  SavedPromptViewSet:                                    │    │
│  │  - create() → POST /saved-prompts/                      │    │
│  │  - list() → GET /saved-prompts/                         │    │
│  │  - retrieve() → GET /saved-prompts/{id}/                │    │
│  │  - update() → PATCH /saved-prompts/{id}/                │    │
│  │  - destroy() → DELETE /saved-prompts/{id}/              │    │
│  │  - toggle_favorite() → POST /{id}/toggle-favorite/      │    │
│  │  - use() → POST /{id}/use/                              │    │
│  │                                                          │    │
│  │  GraphQL Resolvers:                                     │    │
│  │  - Query.savedPrompts()                                 │    │
│  │  - Query.savedPrompt()                                  │    │
│  │  - Mutation.createSavedPrompt()                         │    │
│  │  - Mutation.updateSavedPrompt()                         │    │
│  │  - Mutation.toggleFavoriteSavedPrompt()                 │    │
│  └──────────────────────────┬───────────────────────────────┘    │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐    │
│  │           Business Logic / Service Layer                │    │
│  │                                                          │    │
│  │  PromptManagementService:                              │    │
│  │  - save_prompt(user, data) → SavedPrompt               │    │
│  │  - get_user_prompts(user) → QuerySet                   │    │
│  │  - search_prompts(user, query) → QuerySet              │    │
│  │  - toggle_favorite(user, prompt_id) → bool             │    │
│  │  - record_usage(user, prompt_id) → void                │    │
│  │                                                          │    │
│  │  ValidationService:                                    │    │
│  │  - validate_title(title) → bool                        │    │
│  │  - validate_content(content) → bool                    │    │
│  │  - validate_tags(tags) → List[str]                     │    │
│  │                                                          │    │
│  │  SearchService:                                        │    │
│  │  - full_text_search(query) → QuerySet                  │    │
│  │  - filter_by_category(category) → QuerySet             │    │
│  │  - filter_by_tags(tags) → QuerySet                     │    │
│  └──────────────────────────┬───────────────────────────────┘    │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐    │
│  │             Data Models (ORM Layer)                     │    │
│  │                                                          │    │
│  │  SavedPrompt:                                           │    │
│  │  ├─ Fields:                                             │    │
│  │  │  - id (UUID)                                         │    │
│  │  │  - user_id (Foreign Key)                             │    │
│  │  │  - title (String, max 200)                           │    │
│  │  │  - content (Text)                                    │    │
│  │  │  - description (Text)                                │    │
│  │  │  - category (String)                                 │    │
│  │  │  - tags (JSON Array)                                 │    │
│  │  │  - use_count (Integer)                               │    │
│  │  │  - last_used_at (DateTime)                           │    │
│  │  │  - is_favorite (Boolean)                             │    │
│  │  │  - is_public (Boolean)                               │    │
│  │  │  - is_deleted (Boolean, soft delete)                 │    │
│  │  │  - created_at (DateTime)                             │    │
│  │  │  - updated_at (DateTime)                             │    │
│  │  │                                                       │    │
│  │  ├─ Relationships:                                      │    │
│  │  │  - user (Many-to-One)                                │    │
│  │  │  - history_entries (One-to-Many)                     │    │
│  │  │                                                       │    │
│  │  ├─ Methods:                                            │    │
│  │  │  - increment_use_count()                             │    │
│  │  │  - toggle_favorite()                                 │    │
│  │  │  - soft_delete()                                    │    │
│  │  │  - duplicate()                                       │    │
│  │  │                                                       │    │
│  │  ├─ Indexes:                                            │    │
│  │  │  - user + created_at                                 │    │
│  │  │  - user + category                                   │    │
│  │  │  - user + is_favorite                                │    │
│  │  │  - use_count                                         │    │
│  │  │  - is_deleted                                        │    │
│  │  │                                                       │    │
│  │  PromptHistory (Link to usage tracking):                │    │
│  │  ├─ saved_prompt (Foreign Key → SavedPrompt)            │    │
│  │  ├─ source (e.g., 'saved_prompt', 'manual')             │    │
│  │  ├─ usage metadata                                      │    │
│  │  └─ timestamps                                          │    │
│  └──────────────────────────┬───────────────────────────────┘    │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
           ┌────────▼────────┐   ┌────▼─────────┐
           │  SQLite/        │   │  Cache       │
           │  PostgreSQL     │   │  (Redis)     │
           │  Database       │   │  Optional    │
           │                 │   │              │
           │  saved_prompts  │   │ Cached:      │
           │  prompt_history │   │ - User       │
           │  user_intents   │   │   categories │
           │  prompt_library │   │ - Popular    │
           │                 │   │   tags       │
           └─────────────────┘   │ - Top prompts│
                                 └──────────────┘
```

---

## 2. Data Flow Diagram

### Saving a Prompt Flow

```
START
  │
  ├─► User enters prompt in chat
  │   │
  │   └─► User clicks "Save Prompt" button
  │       │
  │       ├─► SavePromptModal opens
  │       │
  │       ├─► Auto-populate:
  │       │   ├─ content field ← prompt from textarea
  │       │   └─ timestamp field
  │       │
  │       ├─► User manually enters:
  │       │   ├─ title (required)
  │       │   ├─ description (optional)
  │       │   ├─ category (dropdown)
  │       │   └─ tags (multi-select)
  │       │
  │       ├─► Frontend Validation:
  │       │   ├─ title != empty
  │       │   ├─ title.length ≤ 200
  │       │   ├─ content != empty
  │       │   ├─ category in valid list
  │       │   ├─ tags.length ≤ 20
  │       │   └─ IF invalid → Show error toast → GOTO user manually enters
  │       │
  │       ├─► User clicks "Save Prompt" button
  │       │
  │       ├─► Frontend sends POST request:
  │       │   {
  │       │     "title": "...",
  │       │     "content": "...",
  │       │     "description": "...",
  │       │     "category": "...",
  │       │     "tags": [...]
  │       │   }
  │       │
  │       ├─► Backend receives request
  │       │   │
  │       │   ├─► Check Authentication
  │       │   │   └─ IF not authenticated → Return 401 → Show error toast
  │       │   │
  │       │   ├─► Validate input (again)
  │       │   │   └─ IF invalid → Return 400 with errors → Show error messages
  │       │   │
  │       │   ├─► Create SavedPrompt record:
  │       │   │   ├─ Set user = current_user
  │       │   │   ├─ Set title = input.title
  │       │   │   ├─ Set content = input.content
  │       │   │   ├─ Set category = input.category
  │       │   │   ├─ Set tags = input.tags
  │       │   │   ├─ Set use_count = 0
  │       │   │   ├─ Set is_favorite = false
  │       │   │   ├─ Set is_deleted = false
  │       │   │   └─ Set created_at = now()
  │       │   │
  │       │   ├─► Save to database
  │       │   │
  │       │   ├─► Return 201 Created with SavedPrompt object
  │       │   │
  │       │   └─► Invalidate cache:
  │       │       ├─ user_{user_id}_prompts
  │       │       ├─ user_{user_id}_categories
  │       │       └─ user_{user_id}_top_tags
  │       │
  │       ├─► Frontend receives response (201)
  │       │   │
  │       │   ├─► Show success toast:
  │       │   │   "Prompt saved successfully!"
  │       │   │
  │       │   ├─► Update local state:
  │       │   │   ├─ Add new prompt to list
  │       │   │   ├─ Clear form fields
  │       │   │   └─ Update category/tag filters
  │       │   │
  │       │   ├─► Close SavePromptModal
  │       │   │
  │       │   └─► Call onSuccess callback (optional)
  │       │
  │       └─► END - Prompt saved successfully!
  │
END
```

### Retrieving Saved Prompts Flow

```
START
  │
  ├─► User navigates to "Saved Prompts" page
  │   │
  │   ├─► SavedPromptsPage component mounts
  │   │
  │   ├─► Component fetches prompts:
  │   │   │
  │   │   ├─ Check cache: cache_key = 'user_{user_id}_prompts'
  │   │   │  ├─ IF cache hit → Return cached results
  │   │   │  └─ ELSE → Continue
  │   │   │
  │   │   ├─ Send GET request to /api/v2/history/saved-prompts/
  │   │   │  Query params: ?page=1&ordering=-updated_at
  │   │   │
  │   │   ├─► Backend receives request
  │   │   │   │
  │   │   │   ├─ Check Authentication
  │   │   │   │  └─ IF not authenticated → Return 401
  │   │   │   │
  │   │   │   ├─ Build QuerySet:
  │   │   │   │  queryset = SavedPrompt.objects.filter(
  │   │   │   │              user = current_user,
  │   │   │   │              is_deleted = false
  │   │   │   │            ).select_related('user')
  │   │   │   │              .order_by('-updated_at')
  │   │   │   │
  │   │   │   ├─ Apply Pagination:
  │   │   │   │  page_size = 10
  │   │   │   │  offset = (page - 1) * 10
  │   │   │   │  prompts = queryset[offset:offset+10]
  │   │   │   │
  │   │   │   ├─ Serialize results
  │   │   │   │
  │   │   │   ├─ Return 200 OK with:
  │   │   │   │  {
  │   │   │   │    "count": 42,
  │   │   │   │    "next": "...?page=2",
  │   │   │   │    "previous": null,
  │   │   │   │    "results": [...]
  │   │   │   │  }
  │   │   │   │
  │   │   │   └─ Cache results (TTL: 5 minutes)
  │   │   │
  │   │   └─ Frontend receives response
  │   │
  │   ├─► Render SavedPromptsPage:
  │   │   │
  │   │   ├─ Category filter dropdown (populated from list)
  │   │   ├─ Tags filter (extracted from results)
  │   │   ├─ Search input box
  │   │   │
  │   │   ├─ Prompt list:
  │   │   │  For each prompt in results:
  │   │   │  ├─ Title (clickable)
  │   │   │  ├─ Category badge
  │   │   │  ├─ Tags display
  │   │   │  ├─ Use count
  │   │   │  ├─ Favorite button (star icon)
  │   │   │  ├─ Edit button (if owned)
  │   │   │  ├─ Delete button (if owned)
  │   │   │  └─ Created date
  │   │   │
  │   │   └─ Pagination controls
  │   │       ├─ Previous page button
  │   │       ├─ Page indicators
  │   │       └─ Next page button
  │   │
  │   ├─► User filters by category:
  │   │   │
  │   │   ├─ User selects category from dropdown
  │   │   │
  │   │   ├─ Send GET request with filter:
  │   │   │  /api/v2/history/saved-prompts/?category=business
  │   │   │
  │   │   ├─ Backend filters:
  │   │   │  queryset = queryset.filter(category='business')
  │   │   │
  │   │   └─ Return filtered results
  │   │
  │   ├─► User searches prompts:
  │   │   │
  │   │   ├─ User types in search box
  │   │   │
  │   │   ├─ Frontend debounces (300ms)
  │   │   │
  │   │   ├─ Send GET request:
  │   │   │  /api/v2/history/saved-prompts/search/?q=email
  │   │   │
  │   │   ├─ Backend full-text search:
  │   │   │  queryset = queryset.filter(
  │   │   │    Q(title__icontains='email') |
  │   │   │    Q(content__icontains='email') |
  │   │   │    Q(description__icontains='email')
  │   │   │  )
  │   │   │
  │   │   └─ Return matching prompts
  │   │
  │   └─► User clicks on a prompt
  │       │
  │       ├─ Modal/page opens with full prompt details:
  │       │  ├─ Title
  │       │  ├─ Full content
  │       │  ├─ Description
  │       │  ├─ Category
  │       │  ├─ Tags
  │       │  ├─ Use count
  │       │  ├─ Last used date
  │       │  └─ Created/Updated dates
  │       │
  │       └─ User can:
  │           ├─ Copy content
  │           ├─ Use prompt (→ insert into chat)
  │           ├─ Edit (→ open edit form)
  │           ├─ Delete (→ soft delete)
  │           ├─ Duplicate (→ create copy)
  │           └─ Mark favorite (→ toggle star)
  │
END
```

---

## 3. Component Relationships

### Component Hierarchy

```
App
├─ ChatPage
│  ├─ ChatInterface (prompt input/output)
│  │  └─ [Save Prompt Button]
│  │     └─ SavePromptModal (Portal)
│  │        ├─ TitleInput
│  │        ├─ DescriptionInput
│  │        ├─ CategorySelect
│  │        ├─ TagsInput
│  │        ├─ PromptPreview
│  │        └─ SubmitButton
│  │
│  └─ SideNav
│     ├─ PromptHistoryLink
│     └─ SavedPromptsLink
│
├─ SavedPromptsPage
│  ├─ SearchBar
│  │  └─ (Triggers: SearchSavedPrompts query)
│  │
│  ├─ FilterSection
│  │  ├─ CategoryFilter
│  │  │  └─ (Triggers: GetSavedPrompts query with category)
│  │  │
│  │  └─ TagsFilter
│  │     └─ (Triggers: GetSavedPrompts query with tags)
│  │
│  ├─ PromptsList
│  │  ├─ PromptCard (×N)
│  │  │  ├─ Title
│  │  │  ├─ Description (truncated)
│  │  │  ├─ Category Badge
│  │  │  ├─ Tags Display
│  │  │  ├─ Stats (use_count, created_at)
│  │  │  └─ Actions
│  │  │     ├─ FavoriteButton
│  │  │     │  └─ (Triggers: ToggleFavoriteSavedPrompt mutation)
│  │  │     ├─ EditButton
│  │  │     │  └─ EditPromptModal
│  │  │     │     └─ (Triggers: UpdateSavedPrompt mutation)
│  │  │     ├─ UseButton
│  │  │     │  └─ (Triggers: UseSavedPrompt mutation)
│  │  │     ├─ DuplicateButton
│  │  │     │  └─ (Triggers: CreateSavedPrompt mutation with copied content)
│  │  │     └─ DeleteButton
│  │  │        └─ (Triggers: DeleteSavedPrompt mutation)
│  │  │
│  │  └─ Pagination
│  │     └─ (Triggers: GetSavedPrompts query with page param)
│  │
│  └─ PromptDetailModal (when card clicked)
│     ├─ FullContent Display
│     ├─ Metadata Display
│     └─ Action Buttons
│
└─ AdminPanel
   └─ SavedPromptAdmin
      ├─ ListVie
      ├─ DetailView
      └─ BulkActions
```

### State Management Flow

```
Redux Store Structure:
{
  prompts: {
    savedPrompts: SavedPrompt[]
    selectedCategory: string
    searchQuery: string
    isLoading: boolean
    error: string | null
    favorites: string[] (IDs)
    pagination: {
      page: number
      totalCount: number
      hasNext: boolean
    }
  },
  
  user: {
    id: string
    token: string
    isAuthenticated: boolean
  }
}

Actions:
- setPrompts(prompts) → Update list
- addPrompt(prompt) → Add new saved prompt
- updatePrompt(id, updates) → Update existing
- deletePrompt(id) → Remove from list
- setSearchQuery(query) → Update search term
- setCategory(category) → Update category filter
- setLoading(bool) → Toggle loading state
- setError(error) → Set error message
- clearCache() → Clear cached data

Selectors:
- selectAllPrompts(state) → SavedPrompt[]
- selectFavoritePrompts(state) → SavedPrompt[]
- selectPromptsByCategory(state, category) → SavedPrompt[]
- selectIsLoading(state) → boolean
- selectError(state) → string | null
```

---

## 4. Database Schema Relationship Diagram

```
┌──────────────────────────────────────────────┐
│              auth_user                       │
├──────────────────────────────────────────────┤
│ id (PK)                                      │
│ username                                     │
│ email                                        │
│ password_hash                                │
│ created_at                                   │
└────────────────┬─────────────────────────────┘
                 │ (1:N)
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌─────────────────────────┐ ┌──────────────────────────┐
│   saved_prompts         │ │   prompt_history         │
├─────────────────────────┤ ├──────────────────────────┤
│ id (PK, UUID)           │ │ id (PK, UUID)            │
│ user_id (FK) ──────────────► user_id (FK)            │
│ title                   │ │ saved_prompt_id (FK) ◄───┐
│ content                 │ │ source                   │
│ description             │ │ original_prompt          │
│ category                │ │ optimized_prompt         │
│ tags (JSON)             │ │ model_used               │
│ use_count               │ │ tokens_input/output      │
│ last_used_at            │ │ credits_spent            │
│ is_favorite             │ │ intent_category          │
│ is_public               │ │ tags (JSON)              │
│ metadata (JSON)         │ │ is_deleted               │
│ is_deleted              │ │ created_at               │
│ created_at (Indexed)    │ │ updated_at               │
│ updated_at              │ └──────────────────────────┘
└─────────────────────────┘
```

---

## 5. Request/Response Cycle

### Complete Example: Save Prompt

```
FRONTEND: User clicks "Save Prompt"
├─ Display SavePromptModal
└─ Await User Input

FRONTEND: User fills form and submits
├─ Validate input (client-side)
│  └─ IF invalid: Show error & stop
│
└─ Send HTTP POST Request:
   POST /api/v2/history/saved-prompts/
   Headers:
     Authorization: Bearer eyJhbGc...
     Content-Type: application/json
   
   Body:
   {
     "title": "Email Marketing Template",
     "content": "Write a compelling email campaign..."
     "category": "business",
     "tags": ["email", "marketing", "template"],
     "metadata": {
       "targetAudience": "tech-savvy",
       "tone": "professional"
     }
   }

BACKEND: Request arrives at SavedPromptViewSet
├─ Authentication check: Verify JWT token
│  └─ Extract user from token
│
├─ Permission check: IsAuthenticated required
│  └─ IF not authenticated: Return 401 Unauthorized
│
├─ Input validation (server-side):
│  ├─ title: required, max 200 chars
│  ├─ content: required
│  ├─ category: must be valid choice
│  ├─ tags: must be list of strings, max 20
│  └─ IF invalid: Return 400 Bad Request with error details
│
├─ Create SavedPrompt instance:
│  saved_prompt = SavedPrompt(
│    user = current_user,
│    title = validated_data['title'],
│    content = validated_data['content'],
│    category = validated_data['category'],
│    tags = validated_data['tags'],
│    metadata = validated_data.get('metadata', {}),
│    use_count = 0,
│    is_favorite = False,
│    is_deleted = False,
│    created_at = timezone.now(),
│    updated_at = timezone.now()
│  )
│
├─ Save to database:
│  saved_prompt.save()
│  └─ Database inserts new row in saved_prompts table
│
├─ Invalidate caches:
│  cache.invalidate('user_{user_id}_prompts')
│  cache.invalidate('user_{user_id}_categories')
│  cache.invalidate('user_{user_id}_favorite_count')
│
└─ Serialize response:
   Serializer returns:
   {
     "id": "550e8400-e29b-41d4-a716-446655440000",
     "user": "user-id",
     "title": "Email Marketing Template",
     "content": "Write a compelling email campaign...",
     "category": "business",
     "tags": ["email", "marketing", "template"],
     "useCount": 0,
     "lastUsedAt": null,
     "isFavorite": false,
     "createdAt": "2026-02-10T10:30:00Z",
     "updatedAt": "2026-02-10T10:30:00Z"
   }

BACKEND: Send HTTP Response
└─ HTTP 201 Created
   Location: /api/v2/history/saved-prompts/550e8400.../
   Body: [serialized data above]

FRONTEND: Receive response (201)
├─ Parse JSON response
├─ Show success toast:
│  "✓ Prompt saved successfully!"
├─ Update local state:
│  ├─ Add new prompt to savedPrompts array
│  ├─ Update category list if new category
│  └─ Update tag list if new tags
├─ Close SavePromptModal
├─ Clear form fields
└─ Call onSuccess callback(savedPrompt)

USER: Sees confirmation and prompt appears in list
```

---

## 6. Error Handling Flow

```
Error Scenarios:

1. Authentication Error (401)
   └─ Backend: User not authenticated
      └─ Frontend: Redirect to login page
         └─ User: Prompted to log in
         
2. Validation Error (400)
   └─ Backend: Invalid input data
      └─ Response includes field-specific errors:
         {
           "title": ["This field is required."],
           "tags": ["Ensure this field has no more than 20 items."]
         }
      └─ Frontend: Display error messages below each field
      └─ User: Can correct and resubmit
      
3. Permission Error (403)
   └─ Backend: User doesn't own the resource
      └─ Frontend: Show modal: "You don't have permission to edit this"
      └─ User: Dismissed and no action taken
      
4. Not Found Error (404)
   └─ Backend: Prompt doesn't exist or already deleted
      └─ Frontend: Show toast: "Prompt not found or already deleted"
      └─ User: Prompted to refresh the page
      
5. Rate Limit Error (429)
   └─ Backend: Too many requests
      └─ Frontend: Show retry button with countdown
      └─ User: Must wait before trying again
      
6. Server Error (500)
   └─ Backend: Unexpected server error
      └─ Frontend: Show error modal with retry option
      └─ User: Can retry or contact support
      └─ Backend: Logs full error for debugging
```

---

## 7. Deployment Architecture

```
Production Environment:

┌─────────────────────────────────────────┐
│      Frontend (React) - Static Site     │
│  Hosted on CDN / Static Server          │
│  ├─ Bundled JS/CSS                      │
│  ├─ Assets (images, fonts)              │
│  └─ index.html                          │
└────────────┬────────────────────────────┘
             │
      [HTTPS with CORS]
             │
┌────────────▼────────────────────────────┐
│    Django Backend API Server            │
│    (Gunicorn + Nginx)                   │
│  ├─ REST API endpoints                  │
│  ├─ GraphQL endpoint                    │
│  ├─ Admin interface                     │
│  └─ Static files                        │
└────────────┬────────────────────────────┘
             │
      [Database Queries]
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼
┌─────────────┐  ┌──────────────┐
│ PostgreSQL  │  │ Redis Cache  │
│ Database    │  │ (Optional)   │
│ (Primary)   │  │              │
└─────────────┘  └──────────────┘

Scaling options:
- Horizontal: Load balancer → Multiple backend instances
- Vertical: Increase server resources
- Caching: Redis for frequently accessed data
- Database: Replication & read replicas
- CDN: Global content delivery
```

---

This document provides a complete visual understanding of how the prompt saving system works across all layers. Use this alongside the technical specification for implementation.

