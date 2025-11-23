# Prompt History API v2

Complete API documentation for prompt history management endpoints.

## Base URL

```
Development: http://localhost:8000/api/v2/history/
Production: https://www.prompt-temple.com/api/v2/history/
```

## Authentication

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

## Endpoints

### 1. Create History Entry

**POST** `/api/v2/history/`

Create a new prompt history record for the authenticated user.

**Request Body:**
```json
{
  "original_prompt": "Draft an email to a new customer about our product launch",
  "source": "library",
  "intent_category": "email",
  "tags": ["sales", "outreach", "product"],
  "meta": {
    "session_id": "abc123",
    "device": "web"
  }
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user": 1,
  "source": "library",
  "original_prompt": "Draft an email to a new customer about our product launch",
  "optimized_prompt": "",
  "model_used": "",
  "tokens_input": 0,
  "tokens_output": 0,
  "credits_spent": 0,
  "intent_category": "email",
  "tags": ["sales", "outreach", "product"],
  "meta": {
    "session_id": "abc123",
    "device": "web"
  },
  "is_deleted": false,
  "created_at": "2025-11-23T10:30:00Z",
  "updated_at": "2025-11-23T10:30:00Z"
}
```

**Validation:**
- `original_prompt`: Required, max 16,000 characters
- `tags`: Optional, max 20 tags
- `source`: Optional, common values: `library`, `template`, `raw`, `extension`
- `intent_category`: Optional

---

### 2. List History

**GET** `/api/v2/history/`

List all prompt history entries for the authenticated user. Supports filtering, search, and pagination.

**Query Parameters:**
- `intent_category` - Filter by intent category
- `source` - Filter by source
- `search` - Search in original_prompt text
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)
- `ordering` - Sort field (e.g., `-created_at`, `updated_at`)

**Example Request:**
```bash
curl -X GET \
  'http://localhost:8000/api/v2/history/?intent_category=email&page=1' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Response (200 OK):**
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v2/history/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user": 1,
      "source": "library",
      "original_prompt": "Draft an email...",
      "optimized_prompt": "",
      "model_used": "",
      "tokens_input": 0,
      "tokens_output": 0,
      "credits_spent": 0,
      "intent_category": "email",
      "tags": ["sales", "outreach"],
      "meta": {},
      "is_deleted": false,
      "created_at": "2025-11-23T10:30:00Z",
      "updated_at": "2025-11-23T10:30:00Z"
    }
  ]
}
```

---

### 3. Retrieve Single Entry

**GET** `/api/v2/history/{id}/`

Get details of a specific prompt history entry.

**Example Request:**
```bash
curl -X GET \
  'http://localhost:8000/api/v2/history/550e8400-e29b-41d4-a716-446655440000/' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user": 1,
  "source": "library",
  "original_prompt": "Draft an email to a new customer about our product launch",
  "optimized_prompt": "You are a professional sales copywriter...",
  "model_used": "gpt-4o-mini",
  "tokens_input": 512,
  "tokens_output": 246,
  "credits_spent": 3,
  "intent_category": "email",
  "tags": ["sales", "outreach", "product"],
  "meta": {
    "session_id": "abc123",
    "latency_ms": 820
  },
  "is_deleted": false,
  "created_at": "2025-11-23T10:30:00Z",
  "updated_at": "2025-11-23T10:45:00Z"
}
```

---

### 4. Update Entry

**PATCH** `/api/v2/history/{id}/`

Update a prompt history entry (tags, meta, etc.).

**Request Body:**
```json
{
  "tags": ["sales", "email", "follow-up"],
  "meta": {
    "session_id": "abc123",
    "notes": "Used for client onboarding"
  }
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user": 1,
  "tags": ["sales", "email", "follow-up"],
  "meta": {
    "session_id": "abc123",
    "notes": "Used for client onboarding"
  },
  ...
}
```

---

### 5. Soft Delete Entry

**DELETE** `/api/v2/history/{id}/`

Soft-delete a prompt history entry (sets `is_deleted=true`, row remains in database).

**Example Request:**
```bash
curl -X DELETE \
  'http://localhost:8000/api/v2/history/550e8400-e29b-41d4-a716-446655440000/' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Response (204 No Content)**

The entry will be excluded from list queries but remains in the database for audit purposes.

---

### 6. Enhance Prompt (AI Optimization)

**POST** `/api/v2/history/{id}/enhance/`

Run AI-powered prompt enhancement using LangChain. This action:
- Uses credits from user's balance
- Fills `optimized_prompt` field
- Updates token counts and model info
- Records telemetry via LangSmith (if configured)

**Request Body:**
```json
{
  "model": "gpt-4o-mini",
  "style": "concise",
  "session_id": "abc123"
}
```

**Response (200 OK):**
```json
{
  "optimized_prompt": "You are a professional sales copywriter crafting personalized outreach. Write a compelling email to introduce our new product launch to a customer. Focus on:\n- Value proposition\n- Key features\n- Clear call-to-action\n\nTone: Professional yet friendly\nLength: 150-200 words",
  "model_used": "gpt-4o-mini",
  "tokens_input": 512,
  "tokens_output": 246,
  "credits_spent": 3,
  "meta": {
    "latency_ms": 820,
    "user_hash": "a3f5d8c1b2e4",
    "session_id": "abc123",
    "suggestions": [
      "Consider adding personalization tokens",
      "Include product benefits early"
    ]
  }
}
```

**Error Responses:**
- `402 Payment Required` - Insufficient credits
- `403 Forbidden` - Not the owner or AI disabled
- `500 Internal Server Error` - Enhancement failed

---

## Error Handling

All endpoints return standard DRF error responses:

**400 Bad Request:**
```json
{
  "original_prompt": ["This field may not be blank."],
  "tags": ["Maximum 20 tags allowed"]
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

---

## Usage Examples

### Complete Workflow

```bash
# 1. Create history entry
HISTORY_ID=$(curl -X POST \
  'http://localhost:8000/api/v2/history/' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "original_prompt": "Write a blog post about AI",
    "source": "raw",
    "intent_category": "content_creation",
    "tags": ["blog", "ai"]
  }' | jq -r '.id')

# 2. Enhance the prompt
curl -X POST \
  "http://localhost:8000/api/v2/history/${HISTORY_ID}/enhance/" \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-4o-mini",
    "style": "concise"
  }'

# 3. Retrieve updated entry
curl -X GET \
  "http://localhost:8000/api/v2/history/${HISTORY_ID}/" \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'

# 4. List all entries with filter
curl -X GET \
  'http://localhost:8000/api/v2/history/?intent_category=content_creation&ordering=-created_at' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

---

## Permissions

- **List/Create**: Requires authenticated user
- **Retrieve/Update/Delete**: Owner only (or staff)
- **Enhance**: Owner only, requires sufficient credits

---

## Rate Limits

Standard DRF throttling applies:
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- AI enhance: 5 requests/min (due to cost)

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- UUIDs are returned as strings
- Soft-deleted entries are excluded from list queries
- Enhancement pipeline uses environment-configured model (default: `gpt-3.5-turbo`)
- LangSmith tracing requires `LANGCHAIN_TRACING_V2=true` in environment
