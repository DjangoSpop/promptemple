/**
 * GraphQL Frontend Integration Examples
 * Complete client-side implementation for prompt iteration tracking
 */

// ============================================================================
// Apollo Client Setup
// ============================================================================

import { ApolloClient, InMemoryCache, createHttpLink, ApolloProvider } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

// Create HTTP link to GraphQL endpoint
const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_API_URL + '/api/graphql/',
});

// Add authentication token to requests
const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('access_token');
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : "",
    }
  }
});

// Create Apollo Client
export const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
});

// Wrap your app with ApolloProvider
// <ApolloProvider client={apolloClient}>
//   <YourApp />
// </ApolloProvider>

// ============================================================================
// GraphQL Queries and Mutations
// ============================================================================

import { gql } from '@apollo/client';

// Query: Get all iterations for a prompt
export const GET_PROMPT_ITERATIONS = gql`
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
      responseTimeMs
      userRating
      feedbackNotes
      changesSummary
      tags
      isActive
      isBookmarked
      createdAt
      iterationChainLength
      hasNextIteration
    }
  }
`;

// Query: Get latest iteration
export const GET_LATEST_ITERATION = gql`
  query GetLatestIteration($parentPromptId: UUID!) {
    latestIteration(parentPromptId: $parentPromptId) {
      id
      iterationNumber
      promptText
      aiResponse
      responseModel
      tokensInput
      tokensOutput
      creditsSpent
      isActive
      createdAt
    }
  }
`;

// Query: Search iterations
export const SEARCH_ITERATIONS = gql`
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
`;

// Query: Get bookmarked iterations
export const GET_BOOKMARKED_ITERATIONS = gql`
  query GetBookmarkedIterations($limit: Int) {
    bookmarkedIterations(limit: $limit) {
      id
      iterationNumber
      promptText
      aiResponse
      userRating
      feedbackNotes
      tags
      createdAt
      parentPrompt {
        id
        originalPrompt
      }
    }
  }
`;

// Query: Get conversation threads
export const GET_CONVERSATION_THREADS = gql`
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
`;

// Mutation: Create iteration
export const CREATE_ITERATION = gql`
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
`;

// Mutation: Update iteration
export const UPDATE_ITERATION = gql`
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
`;

// Mutation: Set active iteration
export const SET_ACTIVE_ITERATION = gql`
  mutation SetActiveIteration($iterationId: UUID!) {
    setActiveIteration(iterationId: $iterationId) {
      success
      message
      iteration {
        id
        isActive
      }
    }
  }
`;

// Mutation: Delete iteration
export const DELETE_ITERATION = gql`
  mutation DeleteIteration($iterationId: UUID!) {
    deletePromptIteration(iterationId: $iterationId) {
      success
      message
    }
  }
`;

// Mutation: Create conversation thread
export const CREATE_THREAD = gql`
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
`;

// ============================================================================
// React Components
// ============================================================================

import { useQuery, useMutation } from '@apollo/client';
import { useState } from 'react';

// Component: Display iteration history
export function IterationHistory({ promptId }) {
  const { data, loading, error, refetch } = useQuery(GET_PROMPT_ITERATIONS, {
    variables: { parentPromptId: promptId },
  });

  const [setActive] = useMutation(SET_ACTIVE_ITERATION, {
    refetchQueries: [{ query: GET_PROMPT_ITERATIONS, variables: { parentPromptId: promptId } }],
  });

  const handleSetActive = async (iterationId) => {
    try {
      await setActive({ variables: { iterationId } });
    } catch (error) {
      console.error('Error setting active iteration:', error);
    }
  };

  if (loading) return <div>Loading iterations...</div>;
  if (error) return <div>Error loading iterations: {error.message}</div>;

  const iterations = data?.allIterationsForPrompt || [];

  return (
    <div className="iteration-history">
      <h2>Iteration History ({iterations.length})</h2>
      {iterations.map((iteration) => (
        <div key={iteration.id} className={`iteration ${iteration.isActive ? 'active' : ''}`}>
          <div className="iteration-header">
            <span className="iteration-number">v{iteration.iterationNumber}</span>
            {iteration.versionTag && <span className="version-tag">{iteration.versionTag}</span>}
            {iteration.isActive && <span className="badge-active">Active</span>}
            {iteration.isBookmarked && <span className="badge-bookmarked">⭐</span>}
          </div>
          
          <div className="iteration-content">
            <div className="prompt">
              <strong>Prompt:</strong>
              <p>{iteration.promptText}</p>
            </div>
            
            <div className="response">
              <strong>Response:</strong>
              <p>{iteration.aiResponse}</p>
            </div>
          </div>
          
          <div className="iteration-meta">
            <span>Type: {iteration.interactionType}</span>
            <span>Tokens: {iteration.tokensInput + iteration.tokensOutput}</span>
            <span>Credits: {iteration.creditsSpent}</span>
            {iteration.userRating && <span>Rating: {'⭐'.repeat(iteration.userRating)}</span>}
          </div>
          
          {iteration.changesSummary && (
            <div className="changes-summary">
              <strong>Changes:</strong> {iteration.changesSummary}
            </div>
          )}
          
          {!iteration.isActive && (
            <button onClick={() => handleSetActive(iteration.id)}>
              Set as Active
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

// Component: Create new iteration
export function CreateIterationForm({ promptId, onSuccess }) {
  const [promptText, setPromptText] = useState('');
  const [systemMessage, setSystemMessage] = useState('');
  const [tags, setTags] = useState('');

  const [createIteration, { loading }] = useMutation(CREATE_ITERATION, {
    refetchQueries: [{ query: GET_PROMPT_ITERATIONS, variables: { parentPromptId: promptId } }],
    onCompleted: (data) => {
      if (data.createPromptIteration.success) {
        setPromptText('');
        setSystemMessage('');
        setTags('');
        onSuccess?.(data.createPromptIteration.iteration);
      }
    },
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await createIteration({
        variables: {
          input: {
            parentPromptId: promptId,
            promptText,
            systemMessage,
            interactionType: 'manual',
            tags: tags.split(',').map(t => t.trim()).filter(Boolean),
          },
        },
      });
    } catch (error) {
      console.error('Error creating iteration:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="create-iteration-form">
      <div className="form-group">
        <label>Prompt Text:</label>
        <textarea
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          required
          rows={4}
          placeholder="Enter your prompt..."
        />
      </div>

      <div className="form-group">
        <label>System Message (optional):</label>
        <textarea
          value={systemMessage}
          onChange={(e) => setSystemMessage(e.target.value)}
          rows={2}
          placeholder="System instructions..."
        />
      </div>

      <div className="form-group">
        <label>Tags (comma-separated):</label>
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="ai, education, beginner"
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Creating...' : 'Create Iteration'}
      </button>
    </form>
  );
}

// Component: Iteration rating and feedback
export function IterationFeedback({ iterationId }) {
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [isBookmarked, setIsBookmarked] = useState(false);

  const [updateIteration, { loading }] = useMutation(UPDATE_ITERATION);

  const handleSubmit = async () => {
    try {
      await updateIteration({
        variables: {
          input: {
            iterationId,
            userRating: rating,
            feedbackNotes: feedback,
            isBookmarked,
          },
        },
      });
    } catch (error) {
      console.error('Error updating iteration:', error);
    }
  };

  return (
    <div className="iteration-feedback">
      <div className="rating">
        <label>Rate this iteration:</label>
        <div className="stars">
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              className={star <= rating ? 'star-filled' : 'star-empty'}
              onClick={() => setRating(star)}
            >
              ⭐
            </span>
          ))}
        </div>
      </div>

      <div className="feedback">
        <label>Feedback:</label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Share your thoughts..."
          rows={3}
        />
      </div>

      <div className="bookmark">
        <label>
          <input
            type="checkbox"
            checked={isBookmarked}
            onChange={(e) => setIsBookmarked(e.target.checked)}
          />
          Bookmark this iteration
        </label>
      </div>

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? 'Saving...' : 'Save Feedback'}
      </button>
    </div>
  );
}

// Component: Search iterations
export function IterationSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);

  const { data, loading, refetch } = useQuery(SEARCH_ITERATIONS, {
    variables: {
      query: searchQuery,
      tags: selectedTags,
      limit: 20,
    },
    skip: !searchQuery,
  });

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery) {
      refetch();
    }
  };

  return (
    <div className="iteration-search">
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search iterations..."
        />
        <button type="submit">Search</button>
      </form>

      {loading && <div>Searching...</div>}

      {data?.searchIterations && (
        <div className="search-results">
          <h3>Found {data.searchIterations.length} results</h3>
          {data.searchIterations.map((iteration) => (
            <div key={iteration.id} className="search-result">
              <div className="result-header">
                <span>Iteration #{iteration.iterationNumber}</span>
                <span className="type">{iteration.interactionType}</span>
              </div>
              <p>{iteration.promptText}</p>
              <div className="tags">
                {iteration.tags.map((tag) => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Component: Conversation thread viewer
export function ConversationThreadViewer({ threadId }) {
  const { data, loading, error } = useQuery(gql`
    query GetThread($threadId: UUID!) {
      conversationThread(id: $threadId) {
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
            tokensInput
            tokensOutput
          }
        }
      }
    }
  `, {
    variables: { threadId },
  });

  if (loading) return <div>Loading thread...</div>;
  if (error) return <div>Error: {error.message}</div>;

  const thread = data?.conversationThread;
  if (!thread) return <div>Thread not found</div>;

  return (
    <div className="conversation-thread">
      <div className="thread-header">
        <h2>{thread.title}</h2>
        <p>{thread.description}</p>
        <div className="thread-stats">
          <span>{thread.totalIterations} messages</span>
          <span>{thread.totalTokens} tokens</span>
          <span>{thread.totalCredits} credits</span>
        </div>
      </div>

      <div className="thread-messages">
        {thread.messages.map((message) => (
          <div key={message.id} className="thread-message">
            <div className="message-number">#{message.messageOrder}</div>
            <div className="message-content">
              <div className="user-prompt">
                <strong>You:</strong>
                <p>{message.iteration.promptText}</p>
              </div>
              <div className="ai-response">
                <strong>AI:</strong>
                <p>{message.iteration.aiResponse}</p>
              </div>
            </div>
            <div className="message-meta">
              <span>{new Date(message.iteration.createdAt).toLocaleString()}</span>
              <span>
                {message.iteration.tokensInput + message.iteration.tokensOutput} tokens
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Custom Hooks
// ============================================================================

// Hook: Manage prompt iterations
export function usePromptIterations(promptId) {
  const { data, loading, error, refetch } = useQuery(GET_PROMPT_ITERATIONS, {
    variables: { parentPromptId: promptId },
  });

  const [createIteration] = useMutation(CREATE_ITERATION, {
    refetchQueries: [{ query: GET_PROMPT_ITERATIONS, variables: { parentPromptId: promptId } }],
  });

  const [updateIteration] = useMutation(UPDATE_ITERATION);
  const [deleteIteration] = useMutation(DELETE_ITERATION);
  const [setActive] = useMutation(SET_ACTIVE_ITERATION);

  return {
    iterations: data?.allIterationsForPrompt || [],
    loading,
    error,
    refetch,
    createIteration,
    updateIteration,
    deleteIteration,
    setActive,
  };
}

// Hook: Get latest iteration
export function useLatestIteration(promptId) {
  const { data, loading, error } = useQuery(GET_LATEST_ITERATION, {
    variables: { parentPromptId: promptId },
  });

  return {
    latestIteration: data?.latestIteration,
    loading,
    error,
  };
}

export default {
  apolloClient,
  IterationHistory,
  CreateIterationForm,
  IterationFeedback,
  IterationSearch,
  ConversationThreadViewer,
  usePromptIterations,
  useLatestIteration,
};
