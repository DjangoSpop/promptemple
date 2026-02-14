"""
GraphQL Schema for Prompt History and Iteration Management
"""
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q
from .models import PromptHistory, PromptIteration, ConversationThread, ThreadMessage, SavedPrompt


# ==================== Object Types ====================

class PromptHistoryType(DjangoObjectType):
    """GraphQL type for PromptHistory model"""
    class Meta:
        model = PromptHistory
        fields = (
            'id', 'user', 'source', 'original_prompt', 'optimized_prompt',
            'model_used', 'tokens_input', 'tokens_output', 'credits_spent',
            'intent_category', 'tags', 'meta', 'is_deleted',
            'created_at', 'updated_at', 'iterations'
        )


class PromptIterationType(DjangoObjectType):
    """GraphQL type for PromptIteration model"""
    iteration_chain_length = graphene.Int()
    has_next_iteration = graphene.Boolean()
    
    class Meta:
        model = PromptIteration
        fields = (
            'id', 'user', 'parent_prompt', 'previous_iteration',
            'iteration_number', 'version_tag', 'prompt_text', 'system_message',
            'ai_response', 'response_model', 'interaction_type',
            'tokens_input', 'tokens_output', 'response_time_ms', 'credits_spent',
            'user_rating', 'feedback_notes', 'changes_summary', 'diff_size',
            'parameters', 'tags', 'metadata', 'is_active', 'is_bookmarked',
            'is_deleted', 'created_at', 'updated_at'
        )
    
    def resolve_iteration_chain_length(self, info):
        return self.iteration_chain_length
    
    def resolve_has_next_iteration(self, info):
        return self.has_next_iteration


class ConversationThreadType(DjangoObjectType):
    """GraphQL type for ConversationThread model"""
    class Meta:
        model = ConversationThread
        fields = (
            'id', 'user', 'title', 'description', 'total_iterations',
            'total_tokens', 'total_credits', 'status', 'is_shared',
            'is_deleted', 'created_at', 'updated_at', 'last_activity_at',
            'messages'
        )


class ThreadMessageType(DjangoObjectType):
    """GraphQL type for ThreadMessage model"""
    class Meta:
        model = ThreadMessage
        fields = ('id', 'thread', 'iteration', 'message_order', 'created_at')


class SavedPromptType(DjangoObjectType):
    """GraphQL type for SavedPrompt model - User's saved plain prompts"""
    class Meta:
        model = SavedPrompt
        fields = (
            'id', 'user', 'title', 'content', 'description',
            'category', 'tags', 'use_count', 'last_used_at',
            'is_favorite', 'is_public', 'metadata', 'is_deleted',
            'created_at', 'updated_at'
        )


# ==================== Input Types ====================

class CreatePromptIterationInput(graphene.InputObjectType):
    """Input type for creating a new prompt iteration"""
    parent_prompt_id = graphene.UUID(required=True)
    previous_iteration_id = graphene.UUID(required=False)
    prompt_text = graphene.String(required=True)
    system_message = graphene.String(required=False)
    ai_response = graphene.String(required=False)
    response_model = graphene.String(required=False)
    interaction_type = graphene.String(required=False)
    tokens_input = graphene.Int(required=False)
    tokens_output = graphene.Int(required=False)
    response_time_ms = graphene.Int(required=False)
    credits_spent = graphene.Int(required=False)
    user_rating = graphene.Int(required=False)
    feedback_notes = graphene.String(required=False)
    changes_summary = graphene.String(required=False)
    parameters = graphene.JSONString(required=False)
    tags = graphene.List(graphene.String, required=False)
    metadata = graphene.JSONString(required=False)
    version_tag = graphene.String(required=False)


class UpdatePromptIterationInput(graphene.InputObjectType):
    """Input type for updating an existing prompt iteration"""
    iteration_id = graphene.UUID(required=True)
    prompt_text = graphene.String(required=False)
    system_message = graphene.String(required=False)
    ai_response = graphene.String(required=False)
    user_rating = graphene.Int(required=False)
    feedback_notes = graphene.String(required=False)
    is_bookmarked = graphene.Boolean(required=False)
    tags = graphene.List(graphene.String, required=False)
    metadata = graphene.JSONString(required=False)


class CreateConversationThreadInput(graphene.InputObjectType):
    """Input type for creating a conversation thread"""
    title = graphene.String(required=False)
    description = graphene.String(required=False)
    status = graphene.String(required=False)


class CreateSavedPromptInput(graphene.InputObjectType):
    """Input type for creating a saved prompt"""
    title = graphene.String(required=True)
    content = graphene.String(required=True)
    description = graphene.String(required=False)
    category = graphene.String(required=False)
    tags = graphene.List(graphene.String, required=False)
    is_favorite = graphene.Boolean(required=False)
    is_public = graphene.Boolean(required=False)
    metadata = graphene.JSONString(required=False)


class UpdateSavedPromptInput(graphene.InputObjectType):
    """Input type for updating a saved prompt"""
    prompt_id = graphene.UUID(required=True)
    title = graphene.String(required=False)
    content = graphene.String(required=False)
    description = graphene.String(required=False)
    category = graphene.String(required=False)
    tags = graphene.List(graphene.String, required=False)
    is_favorite = graphene.Boolean(required=False)
    is_public = graphene.Boolean(required=False)
    metadata = graphene.JSONString(required=False)


# ==================== Queries ====================

class Query(graphene.ObjectType):
    # Prompt History Queries
    prompt_history = graphene.Field(
        PromptHistoryType,
        id=graphene.UUID(required=True),
        description="Get a single prompt history by ID"
    )
    all_prompt_histories = graphene.List(
        PromptHistoryType,
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
        description="Get all prompt histories for the authenticated user"
    )
    
    # Prompt Iteration Queries
    prompt_iteration = graphene.Field(
        PromptIterationType,
        id=graphene.UUID(required=True),
        description="Get a single prompt iteration by ID"
    )
    all_iterations_for_prompt = graphene.List(
        PromptIterationType,
        parent_prompt_id=graphene.UUID(required=True),
        include_deleted=graphene.Boolean(default_value=False),
        description="Get all iterations for a specific prompt"
    )
    latest_iteration = graphene.Field(
        PromptIterationType,
        parent_prompt_id=graphene.UUID(required=True),
        description="Get the latest iteration for a prompt"
    )
    bookmarked_iterations = graphene.List(
        PromptIterationType,
        limit=graphene.Int(default_value=20),
        description="Get all bookmarked iterations for the user"
    )
    
    # Conversation Thread Queries
    conversation_thread = graphene.Field(
        ConversationThreadType,
        id=graphene.UUID(required=True),
        description="Get a single conversation thread by ID"
    )
    all_conversation_threads = graphene.List(
        ConversationThreadType,
        status=graphene.String(required=False),
        limit=graphene.Int(default_value=50),
        description="Get all conversation threads for the user"
    )
    
    # Search and Filter
    search_iterations = graphene.List(
        PromptIterationType,
        query=graphene.String(required=True),
        interaction_type=graphene.String(required=False),
        tags=graphene.List(graphene.String, required=False),
        limit=graphene.Int(default_value=20),
        description="Search iterations by text, type, or tags"
    )

    # Saved Prompt Queries (CRUD for plain prompts)
    saved_prompt = graphene.Field(
        SavedPromptType,
        id=graphene.UUID(required=True),
        description="Get a single saved prompt by ID"
    )
    all_saved_prompts = graphene.List(
        SavedPromptType,
        category=graphene.String(required=False),
        is_favorite=graphene.Boolean(required=False),
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
        description="Get all saved prompts for the authenticated user"
    )
    favorite_saved_prompts = graphene.List(
        SavedPromptType,
        limit=graphene.Int(default_value=20),
        description="Get all favorite saved prompts"
    )
    search_saved_prompts = graphene.List(
        SavedPromptType,
        query=graphene.String(required=True),
        category=graphene.String(required=False),
        tags=graphene.List(graphene.String, required=False),
        limit=graphene.Int(default_value=20),
        description="Search saved prompts by text, category, or tags"
    )
    public_saved_prompts = graphene.List(
        SavedPromptType,
        category=graphene.String(required=False),
        limit=graphene.Int(default_value=50),
        description="Get public saved prompts from all users"
    )

    # Resolvers
    def resolve_prompt_history(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        return PromptHistory.objects.filter(id=id, user=user, is_deleted=False).first()

    def resolve_all_prompt_histories(self, info, limit=50, offset=0):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        return PromptHistory.objects.filter(
            user=user, is_deleted=False
        ).order_by('-created_at')[offset:offset+limit]

    def resolve_prompt_iteration(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        return PromptIteration.objects.filter(id=id, user=user, is_deleted=False).first()

    def resolve_all_iterations_for_prompt(self, info, parent_prompt_id, include_deleted=False):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        queryset = PromptIteration.objects.filter(
            parent_prompt_id=parent_prompt_id,
            user=user
        )
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset.order_by('iteration_number')

    def resolve_latest_iteration(self, info, parent_prompt_id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        return PromptIteration.objects.filter(
            parent_prompt_id=parent_prompt_id,
            user=user,
            is_deleted=False
        ).order_by('-iteration_number').first()

    def resolve_bookmarked_iterations(self, info, limit=20):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        return PromptIteration.objects.filter(
            user=user,
            is_bookmarked=True,
            is_deleted=False
        ).order_by('-created_at')[:limit]

    def resolve_conversation_thread(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        return ConversationThread.objects.filter(id=id, user=user, is_deleted=False).first()

    def resolve_all_conversation_threads(self, info, status=None, limit=50):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        queryset = ConversationThread.objects.filter(user=user, is_deleted=False)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-last_activity_at')[:limit]

    def resolve_search_iterations(self, info, query, interaction_type=None, tags=None, limit=20):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        queryset = PromptIteration.objects.filter(user=user, is_deleted=False)
        
        # Text search
        if query:
            queryset = queryset.filter(
                Q(prompt_text__icontains=query) |
                Q(ai_response__icontains=query) |
                Q(changes_summary__icontains=query) |
                Q(feedback_notes__icontains=query)
            )
        
        # Filter by interaction type
        if interaction_type:
            queryset = queryset.filter(interaction_type=interaction_type)
        
        # Filter by tags
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__contains=[tag])
        
        return queryset.order_by('-created_at')[:limit]

    # SavedPrompt Resolvers
    def resolve_saved_prompt(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        return SavedPrompt.objects.filter(id=id, user=user, is_deleted=False).first()

    def resolve_all_saved_prompts(self, info, category=None, is_favorite=None, limit=50, offset=0):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        queryset = SavedPrompt.objects.filter(user=user, is_deleted=False)
        
        if category:
            queryset = queryset.filter(category=category)
        if is_favorite is not None:
            queryset = queryset.filter(is_favorite=is_favorite)
        
        return queryset.order_by('-updated_at')[offset:offset+limit]

    def resolve_favorite_saved_prompts(self, info, limit=20):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        return SavedPrompt.objects.filter(
            user=user,
            is_favorite=True,
            is_deleted=False
        ).order_by('-updated_at')[:limit]

    def resolve_search_saved_prompts(self, info, query, category=None, tags=None, limit=20):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        queryset = SavedPrompt.objects.filter(user=user, is_deleted=False)
        
        # Text search
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(description__icontains=query)
            )
        
        if category:
            queryset = queryset.filter(category=category)
        
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__contains=[tag])
        
        return queryset.order_by('-updated_at')[:limit]

    def resolve_public_saved_prompts(self, info, category=None, limit=50):
        """Get public prompts - available to all authenticated users"""
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")
        
        queryset = SavedPrompt.objects.filter(is_public=True, is_deleted=False)
        
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-use_count', '-updated_at')[:limit]


# ==================== Mutations ====================

class CreatePromptIteration(graphene.Mutation):
    """Create a new prompt iteration"""
    class Arguments:
        input = CreatePromptIterationInput(required=True)
    
    iteration = graphene.Field(PromptIterationType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            return CreatePromptIteration(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Verify parent prompt exists and belongs to user
            parent_prompt = PromptHistory.objects.get(
                id=input.parent_prompt_id,
                user=user,
                is_deleted=False
            )
            
            # Calculate iteration number
            last_iteration = PromptIteration.objects.filter(
                parent_prompt=parent_prompt
            ).order_by('-iteration_number').first()
            
            iteration_number = (last_iteration.iteration_number + 1) if last_iteration else 1
            
            # Get previous iteration if specified
            previous_iteration = None
            if input.get('previous_iteration_id'):
                previous_iteration = PromptIteration.objects.get(
                    id=input.previous_iteration_id,
                    user=user
                )
            
            # Create iteration
            iteration = PromptIteration.objects.create(
                user=user,
                parent_prompt=parent_prompt,
                previous_iteration=previous_iteration,
                iteration_number=iteration_number,
                prompt_text=input.prompt_text,
                system_message=input.get('system_message', ''),
                ai_response=input.get('ai_response', ''),
                response_model=input.get('response_model', ''),
                interaction_type=input.get('interaction_type', 'manual'),
                tokens_input=input.get('tokens_input', 0),
                tokens_output=input.get('tokens_output', 0),
                response_time_ms=input.get('response_time_ms', 0),
                credits_spent=input.get('credits_spent', 0),
                user_rating=input.get('user_rating'),
                feedback_notes=input.get('feedback_notes', ''),
                changes_summary=input.get('changes_summary', ''),
                parameters=input.get('parameters', {}),
                tags=input.get('tags', []),
                metadata=input.get('metadata', {}),
                version_tag=input.get('version_tag', ''),
            )
            
            # Calculate diff size
            iteration.calculate_diff_size()
            iteration.save()
            
            return CreatePromptIteration(
                iteration=iteration,
                success=True,
                message="Iteration created successfully"
            )
        except PromptHistory.DoesNotExist:
            return CreatePromptIteration(
                success=False,
                message="Parent prompt not found"
            )
        except Exception as e:
            return CreatePromptIteration(
                success=False,
                message=f"Error creating iteration: {str(e)}"
            )


class UpdatePromptIteration(graphene.Mutation):
    """Update an existing prompt iteration"""
    class Arguments:
        input = UpdatePromptIterationInput(required=True)
    
    iteration = graphene.Field(PromptIterationType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            return UpdatePromptIteration(
                success=False,
                message="Authentication required"
            )
        
        try:
            iteration = PromptIteration.objects.get(
                id=input.iteration_id,
                user=user,
                is_deleted=False
            )
            
            # Update fields
            if input.get('prompt_text'):
                iteration.prompt_text = input.prompt_text
            if input.get('system_message') is not None:
                iteration.system_message = input.system_message
            if input.get('ai_response') is not None:
                iteration.ai_response = input.ai_response
            if input.get('user_rating') is not None:
                iteration.user_rating = input.user_rating
            if input.get('feedback_notes') is not None:
                iteration.feedback_notes = input.feedback_notes
            if input.get('is_bookmarked') is not None:
                iteration.is_bookmarked = input.is_bookmarked
            if input.get('tags') is not None:
                iteration.tags = input.tags
            if input.get('metadata') is not None:
                iteration.metadata = input.metadata
            
            iteration.save()
            
            return UpdatePromptIteration(
                iteration=iteration,
                success=True,
                message="Iteration updated successfully"
            )
        except PromptIteration.DoesNotExist:
            return UpdatePromptIteration(
                success=False,
                message="Iteration not found"
            )
        except Exception as e:
            return UpdatePromptIteration(
                success=False,
                message=f"Error updating iteration: {str(e)}"
            )


class DeletePromptIteration(graphene.Mutation):
    """Soft delete a prompt iteration"""
    class Arguments:
        iteration_id = graphene.UUID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, iteration_id):
        user = info.context.user
        if not user.is_authenticated:
            return DeletePromptIteration(
                success=False,
                message="Authentication required"
            )
        
        try:
            iteration = PromptIteration.objects.get(
                id=iteration_id,
                user=user
            )
            iteration.soft_delete()
            
            return DeletePromptIteration(
                success=True,
                message="Iteration deleted successfully"
            )
        except PromptIteration.DoesNotExist:
            return DeletePromptIteration(
                success=False,
                message="Iteration not found"
            )


class SetActiveIteration(graphene.Mutation):
    """Set an iteration as the active version"""
    class Arguments:
        iteration_id = graphene.UUID(required=True)
    
    iteration = graphene.Field(PromptIterationType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, iteration_id):
        user = info.context.user
        if not user.is_authenticated:
            return SetActiveIteration(
                success=False,
                message="Authentication required"
            )
        
        try:
            iteration = PromptIteration.objects.get(
                id=iteration_id,
                user=user,
                is_deleted=False
            )
            iteration.set_as_active()
            
            return SetActiveIteration(
                iteration=iteration,
                success=True,
                message="Iteration set as active"
            )
        except PromptIteration.DoesNotExist:
            return SetActiveIteration(
                success=False,
                message="Iteration not found"
            )


class CreateConversationThread(graphene.Mutation):
    """Create a new conversation thread"""
    class Arguments:
        input = CreateConversationThreadInput(required=True)
    
    thread = graphene.Field(ConversationThreadType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            return CreateConversationThread(
                success=False,
                message="Authentication required"
            )
        
        try:
            thread = ConversationThread.objects.create(
                user=user,
                title=input.get('title', ''),
                description=input.get('description', ''),
                status=input.get('status', 'active')
            )
            
            return CreateConversationThread(
                thread=thread,
                success=True,
                message="Conversation thread created successfully"
            )
        except Exception as e:
            return CreateConversationThread(
                success=False,
                message=f"Error creating thread: {str(e)}"
            )


class AddIterationToThread(graphene.Mutation):
    """Add an iteration to a conversation thread"""
    class Arguments:
        thread_id = graphene.UUID(required=True)
        iteration_id = graphene.UUID(required=True)
    
    thread = graphene.Field(ConversationThreadType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, thread_id, iteration_id):
        user = info.context.user
        if not user.is_authenticated:
            return AddIterationToThread(
                success=False,
                message="Authentication required"
            )
        
        try:
            thread = ConversationThread.objects.get(
                id=thread_id,
                user=user,
                is_deleted=False
            )
            iteration = PromptIteration.objects.get(
                id=iteration_id,
                user=user,
                is_deleted=False
            )
            
            thread.add_iteration(iteration)
            
            return AddIterationToThread(
                thread=thread,
                success=True,
                message="Iteration added to thread"
            )
        except (ConversationThread.DoesNotExist, PromptIteration.DoesNotExist):
            return AddIterationToThread(
                success=False,
                message="Thread or iteration not found"
            )


# ==================== SavedPrompt Mutations ====================

class CreateSavedPrompt(graphene.Mutation):
    """Create a new saved prompt"""
    class Arguments:
        input = CreateSavedPromptInput(required=True)
    
    saved_prompt = graphene.Field(SavedPromptType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            return CreateSavedPrompt(
                success=False,
                message="Authentication required"
            )
        
        try:
            saved_prompt = SavedPrompt.objects.create(
                user=user,
                title=input.title,
                content=input.content,
                description=input.get('description', ''),
                category=input.get('category', ''),
                tags=input.get('tags', []),
                is_favorite=input.get('is_favorite', False),
                is_public=input.get('is_public', False),
                metadata=input.get('metadata', {}),
            )
            
            return CreateSavedPrompt(
                saved_prompt=saved_prompt,
                success=True,
                message="Prompt saved successfully"
            )
        except Exception as e:
            return CreateSavedPrompt(
                success=False,
                message=f"Error saving prompt: {str(e)}"
            )


class UpdateSavedPrompt(graphene.Mutation):
    """Update an existing saved prompt"""
    class Arguments:
        input = UpdateSavedPromptInput(required=True)
    
    saved_prompt = graphene.Field(SavedPromptType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            return UpdateSavedPrompt(
                success=False,
                message="Authentication required"
            )
        
        try:
            saved_prompt = SavedPrompt.objects.get(
                id=input.prompt_id,
                user=user,
                is_deleted=False
            )
            
            # Update fields
            if input.get('title'):
                saved_prompt.title = input.title
            if input.get('content'):
                saved_prompt.content = input.content
            if input.get('description') is not None:
                saved_prompt.description = input.description
            if input.get('category') is not None:
                saved_prompt.category = input.category
            if input.get('tags') is not None:
                saved_prompt.tags = input.tags
            if input.get('is_favorite') is not None:
                saved_prompt.is_favorite = input.is_favorite
            if input.get('is_public') is not None:
                saved_prompt.is_public = input.is_public
            if input.get('metadata') is not None:
                saved_prompt.metadata = input.metadata
            
            saved_prompt.save()
            
            return UpdateSavedPrompt(
                saved_prompt=saved_prompt,
                success=True,
                message="Prompt updated successfully"
            )
        except SavedPrompt.DoesNotExist:
            return UpdateSavedPrompt(
                success=False,
                message="Saved prompt not found"
            )
        except Exception as e:
            return UpdateSavedPrompt(
                success=False,
                message=f"Error updating prompt: {str(e)}"
            )


class DeleteSavedPrompt(graphene.Mutation):
    """Soft delete a saved prompt"""
    class Arguments:
        prompt_id = graphene.UUID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, prompt_id):
        user = info.context.user
        if not user.is_authenticated:
            return DeleteSavedPrompt(
                success=False,
                message="Authentication required"
            )
        
        try:
            saved_prompt = SavedPrompt.objects.get(
                id=prompt_id,
                user=user
            )
            saved_prompt.soft_delete()
            
            return DeleteSavedPrompt(
                success=True,
                message="Prompt deleted successfully"
            )
        except SavedPrompt.DoesNotExist:
            return DeleteSavedPrompt(
                success=False,
                message="Saved prompt not found"
            )


class ToggleFavoriteSavedPrompt(graphene.Mutation):
    """Toggle favorite status of a saved prompt"""
    class Arguments:
        prompt_id = graphene.UUID(required=True)
    
    saved_prompt = graphene.Field(SavedPromptType)
    is_favorite = graphene.Boolean()
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, prompt_id):
        user = info.context.user
        if not user.is_authenticated:
            return ToggleFavoriteSavedPrompt(
                success=False,
                message="Authentication required"
            )
        
        try:
            saved_prompt = SavedPrompt.objects.get(
                id=prompt_id,
                user=user,
                is_deleted=False
            )
            new_status = saved_prompt.toggle_favorite()
            
            return ToggleFavoriteSavedPrompt(
                saved_prompt=saved_prompt,
                is_favorite=new_status,
                success=True,
                message=f"Prompt {'added to' if new_status else 'removed from'} favorites"
            )
        except SavedPrompt.DoesNotExist:
            return ToggleFavoriteSavedPrompt(
                success=False,
                message="Saved prompt not found"
            )


class UseSavedPrompt(graphene.Mutation):
    """Mark a saved prompt as used (increments use count)"""
    class Arguments:
        prompt_id = graphene.UUID(required=True)
    
    saved_prompt = graphene.Field(SavedPromptType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, prompt_id):
        user = info.context.user
        if not user.is_authenticated:
            return UseSavedPrompt(
                success=False,
                message="Authentication required"
            )
        
        try:
            saved_prompt = SavedPrompt.objects.get(
                id=prompt_id,
                user=user,
                is_deleted=False
            )
            saved_prompt.increment_use_count()
            
            return UseSavedPrompt(
                saved_prompt=saved_prompt,
                success=True,
                message="Prompt usage recorded"
            )
        except SavedPrompt.DoesNotExist:
            return UseSavedPrompt(
                success=False,
                message="Saved prompt not found"
            )


class DuplicateSavedPrompt(graphene.Mutation):
    """Create a copy of an existing saved prompt"""
    class Arguments:
        prompt_id = graphene.UUID(required=True)
        new_title = graphene.String(required=False)
    
    saved_prompt = graphene.Field(SavedPromptType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, prompt_id, new_title=None):
        user = info.context.user
        if not user.is_authenticated:
            return DuplicateSavedPrompt(
                success=False,
                message="Authentication required"
            )
        
        try:
            original = SavedPrompt.objects.get(
                id=prompt_id,
                user=user,
                is_deleted=False
            )
            
            # Create a copy
            duplicate = SavedPrompt.objects.create(
                user=user,
                title=new_title or f"{original.title} (Copy)",
                content=original.content,
                description=original.description,
                category=original.category,
                tags=original.tags.copy() if original.tags else [],
                is_favorite=False,
                is_public=False,
                metadata=original.metadata.copy() if original.metadata else {},
            )
            
            return DuplicateSavedPrompt(
                saved_prompt=duplicate,
                success=True,
                message="Prompt duplicated successfully"
            )
        except SavedPrompt.DoesNotExist:
            return DuplicateSavedPrompt(
                success=False,
                message="Saved prompt not found"
            )


class Mutation(graphene.ObjectType):
    # Prompt Iteration Mutations
    create_prompt_iteration = CreatePromptIteration.Field()
    update_prompt_iteration = UpdatePromptIteration.Field()
    delete_prompt_iteration = DeletePromptIteration.Field()
    set_active_iteration = SetActiveIteration.Field()
    
    # Conversation Thread Mutations
    create_conversation_thread = CreateConversationThread.Field()
    add_iteration_to_thread = AddIterationToThread.Field()
    
    # SavedPrompt CRUD Mutations
    create_saved_prompt = CreateSavedPrompt.Field()
    update_saved_prompt = UpdateSavedPrompt.Field()
    delete_saved_prompt = DeleteSavedPrompt.Field()
    toggle_favorite_saved_prompt = ToggleFavoriteSavedPrompt.Field()
    use_saved_prompt = UseSavedPrompt.Field()
    duplicate_saved_prompt = DuplicateSavedPrompt.Field()


# ==================== Schema ====================

schema = graphene.Schema(query=Query, mutation=Mutation)
