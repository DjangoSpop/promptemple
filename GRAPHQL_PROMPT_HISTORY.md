# GraphQL Prompt History Integration

Complete GraphQL integration for professional prompt iteration management and conversation history tracking.

## 🚀 Features

### Core Capabilities
- **Iteration Tracking**: Version control for prompts with full history
- **Conversation Threading**: Group related prompts into conversation threads
- **Human-AI Interactions**: Save complete interaction history
- **Performance Metrics**: Track tokens, response time, and credits
- **Quality Management**: Rate and bookmark iterations
- **Flexible Metadata**: Extensible JSON fields for custom data

### Models

#### 1. **PromptIteration**
Tracks individual versions of prompts with:
- Sequential iteration numbering
- Previous iteration linking (chain tracking)
- AI response storage
- Performance metrics (tokens, time, credits)
- User ratings and feedback
- Change tracking and diff sizes
- Flexible tagging and metadata

#### 2. **ConversationThread**
Groups iterations into conversations with:
- Thread title and description
- Aggregate metrics (total iterations, tokens, credits)
- Status management (active, archived, completed)
- Sharing capabilities

#### 3. **ThreadMessage**
Links iterations to threads with ordering

## 📋 Installation

### 1. Install Dependencies
```bash
pip install graphene-django==3.2.0
```

### 2. Run Migrations
```bash
python manage.py makemigrations prompt_history
python manage.py migrate prompt_history
```

### 3. Verify Installation
Access GraphiQL interface (in development):
```
http://localhost:8000/api/graphql/
```

## 🔧 GraphQL API

### Endpoint
```
POST /api/graphql/
```

### Authentication
Include JWT token in Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## 📝 Queries

### Get All Iterations for a Prompt
```graphql
query GetPromptIterations($parentPromptId: UUID!) {
  allIterationsForPrompt(parentPromptId: $parentPromptId) {
    id
    iterationNumber
    versionTag
    promptText
    aiResponse
    interactionType
    tokensInput
    tokensOutput
    creditsSpent
    userRating
    isActive
    isBookmarked
    createdAt
    iterationChainLength
    hasNextIteration
  }
}
```

### Get Latest Iteration
```graphql
query GetLatestIteration($parentPromptId: UUID!) {
  latestIteration(parentPromptId: $parentPromptId) {
    id
    iterationNumber
    promptText
    aiResponse
    responseModel
    tokensInput
    tokensOutput
    createdAt
  }
}
```

### Search Iterations
```graphql
query SearchIterations($query: String!, $tags: [String], $limit: Int) {
  searchIterations(query: $query, tags: $tags, limit: $limit) {
    id
    iterationNumber
    promptText
    aiResponse
    interactionType
    tags
    createdAt
    parentPrompt {
      id
      originalPrompt
    }
  }
}
```

### Get Bookmarked Iterations
```graphql
query GetBookmarkedIterations($limit: Int) {
  bookmarkedIterations(limit: $limit) {
    id
    iterationNumber
    promptText
    aiResponse
    feedbackNotes
    userRating
    createdAt
    parentPrompt {
      id
      originalPrompt
    }
  }
}
```

### Get Conversation Threads
```graphql
query GetConversationThreads($status: String, $limit: Int) {
  allConversationThreads(status: $status, limit: $limit) {
    id
    title
    description
    totalIterations
    totalTokens
    totalCredits
    status
    lastActivityAt
    messages {
      id
      messageOrder
      iteration {
        id
        promptText
        aiResponse
        createdAt
      }
    }
  }
}
```

## ✏️ Mutations

### Create Prompt Iteration
```graphql
mutation CreateIteration($input: CreatePromptIterationInput!) {
  createPromptIteration(input: $input) {
    success
    message
    iteration {
      id
      iterationNumber
      promptText
      aiResponse
      tokensInput
      tokensOutput
      creditsSpent
      createdAt
    }
  }
}
```

**Variables:**
```json
{
  "input": {
    "parentPromptId": "uuid-here",
    "previousIterationId": "uuid-here-optional",
    "promptText": "Explain quantum computing in simple terms",
    "systemMessage": "You are a helpful teacher",
    "aiResponse": "Quantum computing is...",
    "responseModel": "gpt-4",
    "interactionType": "manual",
    "tokensInput": 15,
    "tokensOutput": 250,
    "responseTimeMs": 1200,
    "creditsSpent": 5,
    "tags": ["education", "physics"],
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 500
    },
    "versionTag": "v1.0"
  }
}
```

### Update Iteration
```graphql
mutation UpdateIteration($input: UpdatePromptIterationInput!) {
  updatePromptIteration(input: $input) {
    success
    message
    iteration {
      id
      userRating
      feedbackNotes
      isBookmarked
      tags
    }
  }
}
```

**Variables:**
```json
{
  "input": {
    "iterationId": "uuid-here",
    "userRating": 5,
    "feedbackNotes": "Excellent explanation!",
    "isBookmarked": true,
    "tags": ["education", "physics", "beginner-friendly"]
  }
}
```

### Set Active Iteration
```graphql
mutation SetActive($iterationId: UUID!) {
  setActiveIteration(iterationId: $iterationId) {
    success
    message
    iteration {
      id
      isActive
    }
  }
}
```

### Create Conversation Thread
```graphql
mutation CreateThread($input: CreateConversationThreadInput!) {
  createConversationThread(input: $input) {
    success
    message
    thread {
      id
      title
      description
      status
      createdAt
    }
  }
}
```

**Variables:**
```json
{
  "input": {
    "title": "Learning Quantum Computing",
    "description": "A conversation thread about quantum computing basics",
    "status": "active"
  }
}
```

### Add Iteration to Thread
```graphql
mutation AddToThread($threadId: UUID!, $iterationId: UUID!) {
  addIterationToThread(threadId: $threadId, iterationId: $iterationId) {
    success
    message
    thread {
      id
      totalIterations
      totalTokens
      totalCredits
    }
  }
}
```

### Delete Iteration (Soft Delete)
```graphql
mutation DeleteIteration($iterationId: UUID!) {
  deletePromptIteration(iterationId: $iterationId) {
    success
    message
  }
}
```

## 💡 Usage Examples

### Example 1: Creating an Iteration Chain

```graphql
# 1. Create first iteration
mutation {
  createPromptIteration(input: {
    parentPromptId: "parent-uuid"
    promptText: "Write a poem about AI"
    aiResponse: "In circuits deep and code so bright..."
    interactionType: "manual"
    tokensInput: 10
    tokensOutput: 100
    creditsSpent: 2
  }) {
    success
    iteration {
      id
      iterationNumber
    }
  }
}

# 2. Create second iteration based on first
mutation {
  createPromptIteration(input: {
    parentPromptId: "parent-uuid"
    previousIterationId: "first-iteration-uuid"
    promptText: "Write a poem about AI in haiku format"
    aiResponse: "Digital minds think..."
    interactionType: "refinement"
    tokensInput: 12
    tokensOutput: 50
    creditsSpent: 1
    changesSummary: "Changed format to haiku"
  }) {
    success
    iteration {
      id
      iterationNumber
    }
  }
}
```

### Example 2: Building a Conversation Thread

```graphql
# 1. Create thread
mutation {
  createConversationThread(input: {
    title: "AI Learning Session"
    description: "Learning about AI concepts"
    status: "active"
  }) {
    success
    thread {
      id
    }
  }
}

# 2. Add iterations to thread
mutation {
  addIterationToThread(
    threadId: "thread-uuid"
    iterationId: "iteration-1-uuid"
  ) {
    success
    thread {
      totalIterations
    }
  }
}
```

### Example 3: Full Iteration History Query

```graphql
query GetFullHistory($promptId: UUID!) {
  allIterationsForPrompt(parentPromptId: $promptId) {
    id
    iterationNumber
    versionTag
    promptText
    aiResponse
    interactionType
    tokensInput
    tokensOutput
    responseTimeMs
    creditsSpent
    userRating
    feedbackNotes
    changesSummary
    diffSize
    tags
    isActive
    isBookmarked
    createdAt
    previousIteration {
      id
      iterationNumber
    }
    parentPrompt {
      originalPrompt
      source
    }
  }
}
```

## 🎯 Integration with Existing System

### From Django Views

```python
from apps.prompt_history.models import PromptHistory, PromptIteration

# Create an iteration programmatically
def save_prompt_iteration(user, parent_prompt_id, prompt_text, ai_response):
    parent_prompt = PromptHistory.objects.get(id=parent_prompt_id, user=user)
    
    # Get latest iteration number
    last_iteration = PromptIteration.objects.filter(
        parent_prompt=parent_prompt
    ).order_by('-iteration_number').first()
    
    iteration_number = (last_iteration.iteration_number + 1) if last_iteration else 1
    
    # Create iteration
    iteration = PromptIteration.objects.create(
        user=user,
        parent_prompt=parent_prompt,
        previous_iteration=last_iteration,
        iteration_number=iteration_number,
        prompt_text=prompt_text,
        ai_response=ai_response,
        interaction_type='manual',
        tokens_input=len(prompt_text.split()),
        tokens_output=len(ai_response.split()),
    )
    
    iteration.calculate_diff_size()
    iteration.save()
    
    return iteration
```

### From Frontend (React/Next.js)

```typescript
// graphql/queries.ts
import { gql } from '@apollo/client';

export const GET_PROMPT_ITERATIONS = gql`
  query GetPromptIterations($parentPromptId: UUID!) {
    allIterationsForPrompt(parentPromptId: $parentPromptId) {
      id
      iterationNumber
      promptText
      aiResponse
      createdAt
      isActive
    }
  }
`;

export const CREATE_ITERATION = gql`
  mutation CreateIteration($input: CreatePromptIterationInput!) {
    createPromptIteration(input: $input) {
      success
      message
      iteration {
        id
        iterationNumber
        promptText
      }
    }
  }
`;

// Usage in component
import { useQuery, useMutation } from '@apollo/client';

function PromptIterations({ promptId }) {
  const { data, loading } = useQuery(GET_PROMPT_ITERATIONS, {
    variables: { parentPromptId: promptId }
  });
  
  const [createIteration] = useMutation(CREATE_ITERATION);
  
  const handleCreateIteration = async (promptText, aiResponse) => {
    await createIteration({
      variables: {
        input: {
          parentPromptId: promptId,
          promptText,
          aiResponse,
          interactionType: 'manual'
        }
      }
    });
  };
  
  // Render iterations...
}
```

## 🚢 Deployment to Heroku

### 1. Update requirements.txt (Already Done)
```
graphene-django==3.2.0
graphene==3.3
```

### 2. Environment Variables
No additional environment variables needed for basic GraphQL functionality.

### 3. Deploy
```powershell
# Run from project root
.\deploy_production.ps1

# Or manually
git add .
git commit -m "feat: Add GraphQL prompt iteration tracking"
git push heroku main
```

### 4. Run Migrations on Heroku
```bash
heroku run python manage.py migrate prompt_history
```

### 5. Verify Deployment
```bash
# Check if GraphQL endpoint is accessible
curl -X POST https://your-app.herokuapp.com/api/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"query":"{ __schema { types { name } } }"}'
```

## 🔒 Security Considerations

1. **Authentication**: All GraphQL queries/mutations require authentication
2. **User Isolation**: Users can only access their own data
3. **Soft Deletes**: Deleted iterations are hidden but preserved
4. **Rate Limiting**: Consider adding rate limiting for production
5. **CSRF Protection**: CSRF exempt for GraphQL endpoint (standard practice)

## 📊 Performance Optimization

### Database Indexes
All critical fields are indexed:
- `user + created_at`
- `parent_prompt + iteration_number`
- `is_active + is_deleted`
- `interaction_type`
- `is_bookmarked`

### Query Optimization Tips
```graphql
# Limit results to avoid large queries
query {
  allIterationsForPrompt(parentPromptId: "uuid", limit: 50) {
    # Only select fields you need
    id
    iterationNumber
    promptText
    createdAt
  }
}
```

## 🧪 Testing

### Test GraphQL Endpoint
```bash
# Create test iteration
python manage.py shell
```

```python
from apps.users.models import User
from apps.prompt_history.models import PromptHistory, PromptIteration

# Get or create test user
user = User.objects.first()

# Create parent prompt
parent = PromptHistory.objects.create(
    user=user,
    original_prompt="Test prompt",
    source="test"
)

# Create iteration
iteration = PromptIteration.objects.create(
    user=user,
    parent_prompt=parent,
    iteration_number=1,
    prompt_text="Test iteration",
    ai_response="Test response"
)

print(f"Created iteration: {iteration.id}")
```

## 📈 Monitoring

Track these metrics in production:
- Total iterations created
- Average iterations per prompt
- Most active users
- Popular interaction types
- Credits consumption per iteration
- Response time distribution

## 🎓 Best Practices

1. **Version Tagging**: Use semantic versioning for important iterations
2. **Change Summaries**: Always provide clear change descriptions
3. **Bookmarking**: Encourage users to bookmark successful iterations
4. **Threading**: Group related prompts into conversation threads
5. **Metadata**: Use metadata field for custom application data

## 🔄 Migration Path

For existing prompt history data:
```python
# Migration script to convert existing data
from apps.prompt_history.models import PromptHistory, PromptIteration

for prompt in PromptHistory.objects.all():
    # Create iteration from existing prompt
    PromptIteration.objects.create(
        user=prompt.user,
        parent_prompt=prompt,
        iteration_number=1,
        prompt_text=prompt.original_prompt,
        ai_response=prompt.optimized_prompt,
        tokens_input=prompt.tokens_input,
        tokens_output=prompt.tokens_output,
        credits_spent=prompt.credits_spent,
        interaction_type='manual',
        tags=prompt.tags,
        metadata=prompt.meta
    )
```

## 📚 Additional Resources

- [GraphQL Documentation](https://graphql.org/learn/)
- [Graphene-Django Documentation](https://docs.graphene-python.org/projects/django/)
- [Apollo Client (Frontend)](https://www.apollographql.com/docs/react/)

---

**Ready for MVP deployment!** 🚀

The GraphQL system is fully integrated and ready to be deployed to your Heroku app.
