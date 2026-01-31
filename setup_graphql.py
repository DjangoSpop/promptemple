"""
GraphQL Setup and Testing Script
Automates the setup and testing of GraphQL prompt iteration system
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from apps.users.models import User
from apps.prompt_history.models import PromptHistory, PromptIteration, ConversationThread

def create_test_data():
    """Create test data for GraphQL testing"""
    print("🔧 Creating test data...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='test@promptcraft.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing test user: {user.email}")
    
    # Create parent prompt
    parent_prompt, created = PromptHistory.objects.get_or_create(
        user=user,
        original_prompt="Explain machine learning to a beginner",
        defaults={
            'source': 'graphql_test',
            'model_used': 'gpt-4',
            'tokens_input': 10,
            'tokens_output': 150,
            'credits_spent': 3,
            'intent_category': 'education',
            'tags': ['ai', 'education', 'beginner']
        }
    )
    
    if created:
        print(f"✅ Created parent prompt: {parent_prompt.id}")
    else:
        print(f"✅ Using existing parent prompt: {parent_prompt.id}")
    
    # Create iteration chain
    iterations_data = [
        {
            'prompt_text': 'Explain machine learning to a beginner',
            'ai_response': 'Machine learning is a way for computers to learn from data...',
            'interaction_type': 'manual',
            'tokens_input': 10,
            'tokens_output': 150,
        },
        {
            'prompt_text': 'Explain machine learning to a beginner using simple analogies',
            'ai_response': 'Think of machine learning like teaching a child...',
            'interaction_type': 'refinement',
            'tokens_input': 12,
            'tokens_output': 180,
            'changes_summary': 'Added requirement for simple analogies'
        },
        {
            'prompt_text': 'Explain machine learning using cooking analogies',
            'ai_response': 'Machine learning is like following a recipe...',
            'interaction_type': 'refinement',
            'tokens_input': 9,
            'tokens_output': 200,
            'changes_summary': 'Specified cooking analogies'
        }
    ]
    
    previous_iteration = None
    created_iterations = []
    
    for i, iter_data in enumerate(iterations_data, start=1):
        iteration, created = PromptIteration.objects.get_or_create(
            user=user,
            parent_prompt=parent_prompt,
            iteration_number=i,
            defaults={
                'previous_iteration': previous_iteration,
                'prompt_text': iter_data['prompt_text'],
                'ai_response': iter_data['ai_response'],
                'response_model': 'gpt-4',
                'interaction_type': iter_data['interaction_type'],
                'tokens_input': iter_data['tokens_input'],
                'tokens_output': iter_data['tokens_output'],
                'response_time_ms': 1200,
                'credits_spent': 2,
                'changes_summary': iter_data.get('changes_summary', ''),
                'tags': ['test', 'ml', 'education'],
                'parameters': {'temperature': 0.7, 'max_tokens': 500},
                'is_active': (i == len(iterations_data))  # Last iteration is active
            }
        )
        
        if created:
            iteration.calculate_diff_size()
            iteration.save()
            print(f"✅ Created iteration {i}: {iteration.id}")
        else:
            print(f"✅ Using existing iteration {i}: {iteration.id}")
        
        created_iterations.append(iteration)
        previous_iteration = iteration
    
    # Create conversation thread
    thread, created = ConversationThread.objects.get_or_create(
        user=user,
        title='Learning Machine Learning',
        defaults={
            'description': 'A conversation thread about learning ML concepts',
            'status': 'active'
        }
    )
    
    if created:
        print(f"✅ Created conversation thread: {thread.id}")
        
        # Add iterations to thread
        for iteration in created_iterations:
            thread.add_iteration(iteration)
        
        print(f"✅ Added {len(created_iterations)} iterations to thread")
    else:
        print(f"✅ Using existing conversation thread: {thread.id}")
    
    print("\n📊 Test Data Summary:")
    print(f"   User: {user.email}")
    print(f"   Parent Prompt: {parent_prompt.id}")
    print(f"   Iterations: {len(created_iterations)}")
    print(f"   Thread: {thread.id}")
    print(f"   Total Thread Iterations: {thread.total_iterations}")
    print(f"   Total Thread Tokens: {thread.total_tokens}")
    
    return user, parent_prompt, created_iterations, thread


def print_graphql_example_queries(user, parent_prompt, thread):
    """Print example GraphQL queries for testing"""
    print("\n" + "="*80)
    print("🎯 GRAPHQL TESTING QUERIES")
    print("="*80)
    
    print("\n1️⃣ Get All Iterations for Prompt:")
    print("-" * 80)
    print(f'''
query {{
  allIterationsForPrompt(parentPromptId: "{parent_prompt.id}") {{
    id
    iterationNumber
    promptText
    aiResponse
    interactionType
    tokensInput
    tokensOutput
    creditsSpent
    changesSummary
    isActive
    createdAt
  }}
}}
''')
    
    print("\n2️⃣ Get Latest Iteration:")
    print("-" * 80)
    print(f'''
query {{
  latestIteration(parentPromptId: "{parent_prompt.id}") {{
    id
    iterationNumber
    promptText
    aiResponse
    isActive
  }}
}}
''')
    
    print("\n3️⃣ Search Iterations:")
    print("-" * 80)
    print('''
query {
  searchIterations(query: "machine learning", tags: ["test"], limit: 10) {
    id
    iterationNumber
    promptText
    tags
    createdAt
  }
}
''')
    
    print("\n4️⃣ Get Conversation Thread:")
    print("-" * 80)
    print(f'''
query {{
  conversationThread(id: "{thread.id}") {{
    id
    title
    description
    totalIterations
    totalTokens
    totalCredits
    status
    messages {{
      messageOrder
      iteration {{
        promptText
        aiResponse
      }}
    }}
  }}
}}
''')
    
    print("\n5️⃣ Create New Iteration (Mutation):")
    print("-" * 80)
    print(f'''
mutation {{
  createPromptIteration(input: {{
    parentPromptId: "{parent_prompt.id}"
    promptText: "Explain machine learning with real-world examples"
    aiResponse: "Let's look at spam filters as an example..."
    interactionType: "refinement"
    tokensInput: 11
    tokensOutput: 220
    creditsSpent: 2
    tags: ["test", "ml", "examples"]
    parameters: "{{\\"temperature\\": 0.7}}"
  }}) {{
    success
    message
    iteration {{
      id
      iterationNumber
      promptText
    }}
  }}
}}
''')
    
    print("\n" + "="*80)
    print("📍 GraphQL Endpoint: http://localhost:8000/api/graphql/")
    print("📍 GraphiQL Interface: http://localhost:8000/api/graphql/ (in browser)")
    print("="*80)


def main():
    """Main setup and testing function"""
    print("\n" + "="*80)
    print("🚀 GRAPHQL PROMPT HISTORY SETUP & TEST")
    print("="*80 + "\n")
    
    try:
        # Create test data
        user, parent_prompt, iterations, thread = create_test_data()
        
        # Print example queries
        print_graphql_example_queries(user, parent_prompt, thread)
        
        print("\n✅ Setup complete! You can now:")
        print("   1. Access GraphiQL at http://localhost:8000/api/graphql/")
        print("   2. Use the queries above to test the API")
        print("   3. Get JWT token by logging in with:")
        print(f"      - Email: test@promptcraft.com")
        print(f"      - Password: testpass123")
        print("\n   4. Include JWT in Authorization header:")
        print("      Authorization: Bearer <your_jwt_token>")
        
        print("\n🎉 GraphQL system is ready for deployment!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
