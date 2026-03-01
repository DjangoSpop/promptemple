"""
inflate_templates.py
====================
Idempotent management command to backfill 90 professional developer-focused
prompt templates across 10 categories.

Usage:
    python manage.py inflate_templates
    python manage.py inflate_templates --dry-run --verbose
    python manage.py inflate_templates --category typescript
    python manage.py inflate_templates --rollback
    python manage.py inflate_templates --batch-size 5 --verbose
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.templates.models import Template, TemplateCategory, PromptField, TemplateField

User = get_user_model()

# ── CATEGORIES ────────────────────────────────────────────────────────────────

CATEGORIES_DATASET = [
    {"name": "Frontend Development", "slug": "frontend-dev",
     "description": "React components, hooks, patterns, and UI architecture.",
     "icon": "code", "color": "#3B82F6", "order": 10},
    {"name": "Next.js & React", "slug": "nextjs-react",
     "description": "Next.js App Router, server components, and React patterns.",
     "icon": "triangle", "color": "#1a1a1a", "order": 20},
    {"name": "TypeScript", "slug": "typescript",
     "description": "Type system patterns, utility types, and TS best practices.",
     "icon": "type", "color": "#3178C6", "order": 30},
    {"name": "CSS & Styling", "slug": "css-styling",
     "description": "Tailwind, CSS architecture, animations, and design systems.",
     "icon": "palette", "color": "#06B6D4", "order": 40},
    {"name": "Web Performance", "slug": "web-performance",
     "description": "Core Web Vitals, bundle optimization, and runtime performance.",
     "icon": "zap", "color": "#F59E0B", "order": 50},
    {"name": "Accessibility", "slug": "accessibility",
     "description": "WCAG compliance, ARIA patterns, and inclusive UI engineering.",
     "icon": "eye", "color": "#10B981", "order": 60},
    {"name": "Code Review", "slug": "code-review",
     "description": "PR descriptions, review feedback, refactoring, and tech debt.",
     "icon": "git-pull-request", "color": "#8B5CF6", "order": 70},
    {"name": "API Design", "slug": "api-design",
     "description": "REST, GraphQL, OpenAPI specs, and API architecture patterns.",
     "icon": "server", "color": "#EF4444", "order": 80},
    {"name": "Testing & QA", "slug": "testing-qa",
     "description": "Unit, integration, E2E, visual regression, and TDD workflows.",
     "icon": "check-circle", "color": "#EC4899", "order": 90},
    {"name": "DevOps & CI/CD", "slug": "devops-cicd",
     "description": "GitHub Actions, Docker, Heroku, migrations, and monitoring.",
     "icon": "settings", "color": "#6366F1", "order": 100},
]

# ── TEMPLATES DATASET ─────────────────────────────────────────────────────────
# Rules:
#  • Placeholders: ONLY {{snake_case}} — no uppercase, no spaces.
#  • dropdown / radio fields MUST have a non-empty options list.
#  • default_value for dropdown/radio must be "" or one of the options.

TEMPLATES_DATASET = [

    # ══════════════════════════════════════════════════════════════════════════
    # FRONTEND DEVELOPMENT  (INFL-FE-001 … INFL-FE-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-FE-001",
        "title": "React Functional Component Generator",
        "description": "Scaffold a production-ready React functional component with TypeScript props and JSDoc.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Generate a React functional component named {{component_name}}.\n\n"
            "Props interface:\n{{props_interface}}\n\n"
            "Behavior: {{component_behavior}}\n\n"
            "Styling approach: {{styling_approach}}\n\n"
            "Requirements:\n"
            "- Full TypeScript types\n"
            "- Memoize with React.memo if pure\n"
            "- Named + default export\n"
            "- JSDoc comment block"
        ),
        "tags": ["react", "typescript", "component"],
        "prompt_framework": "CO-STAR", "subcategory": "components",
        "use_cases": ["new feature scaffolding", "design system"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Name", "placeholder": "e.g. UserProfileCard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase name", "options": [], "order": 0},
            {"label": "Props Interface", "placeholder": "userId: string; onEdit: () => void",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "TypeScript prop types", "options": [], "order": 1},
            {"label": "Component Behavior", "placeholder": "What does this component render and do?",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Functional description", "options": [], "order": 2},
            {"label": "Styling Approach", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Tailwind CSS",
             "help_text": "CSS methodology", "options": ["Tailwind CSS", "CSS Modules", "Styled Components", "Inline Styles"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-FE-002",
        "title": "Custom React Hook Builder",
        "description": "Create a reusable custom hook with cleanup, TypeScript generics, and usage example.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Create a custom React hook named {{hook_name}}.\n\n"
            "Purpose: {{hook_purpose}}\n\n"
            "External dependencies: {{dependencies}}\n\n"
            "Return shape: {{return_shape}}\n\n"
            "Requirements:\n"
            "- TypeScript generics where applicable\n"
            "- Proper cleanup in useEffect\n"
            "- Include usage example in JSDoc"
        ),
        "tags": ["react", "hooks", "typescript"], "prompt_framework": "CO-STAR",
        "subcategory": "hooks", "use_cases": ["data fetching", "form state", "browser API"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Hook Name", "placeholder": "e.g. useDebounce",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "camelCase, must start with 'use'", "options": [], "order": 0},
            {"label": "Hook Purpose", "placeholder": "Single responsibility description",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What problem does this hook solve?", "options": [], "order": 1},
            {"label": "Dependencies", "placeholder": "e.g. fetch API, useContext(AuthContext)",
             "field_type": "text", "is_required": False, "default_value": "",
             "help_text": "External APIs or context", "options": [], "order": 2},
            {"label": "Return Shape", "placeholder": "{ data, loading, error, refetch }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "TypeScript return type", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-FE-003",
        "title": "React Context + Provider Pattern",
        "description": "Build a typed Context with Provider, custom hook, and error boundary for missing provider.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Build a React Context system named {{context_name}}.\n\n"
            "State shape: {{state_shape}}\n\n"
            "Provider scope: {{provider_scope}}\n\n"
            "Requirements:\n"
            "- Typed with TypeScript\n"
            "- useContext wrapper hook that throws if used outside provider\n"
            "- Memoize context value to prevent unnecessary re-renders"
        ),
        "tags": ["react", "context", "state", "typescript"], "prompt_framework": "RACE",
        "subcategory": "state-management", "use_cases": ["global state", "feature state"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Context Name", "placeholder": "e.g. AuthContext",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase context name", "options": [], "order": 0},
            {"label": "State Shape", "placeholder": "user: User | null; isLoading: boolean",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "TypeScript interface for context value", "options": [], "order": 1},
            {"label": "Provider Scope", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Feature",
             "help_text": "Where in the tree will this provider live?",
             "options": ["App Root", "Feature", "Page", "Component"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-FE-004",
        "title": "React Error Boundary",
        "description": "Implement a class-based Error Boundary with fallback UI and optional error reporting.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Create a React Error Boundary named {{boundary_name}}.\n\n"
            "Fallback UI: {{fallback_ui}}\n\n"
            "Error reporting service: {{error_service}}\n\n"
            "Requirements:\n"
            "- componentDidCatch logs to {{error_service}}\n"
            "- getDerivedStateFromError updates hasError state\n"
            "- Provide a 'Try Again' reset button in fallback\n"
            "- TypeScript props and state types"
        ),
        "tags": ["react", "error-handling", "resilience"], "prompt_framework": "CO-STAR",
        "subcategory": "error-handling", "use_cases": ["production resilience", "UX recovery"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Boundary Name", "placeholder": "e.g. DashboardErrorBoundary",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase", "options": [], "order": 0},
            {"label": "Fallback UI Description", "placeholder": "Show a centered card with error icon and retry button",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What the user sees on error", "options": [], "order": 1},
            {"label": "Error Reporting Service", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Sentry",
             "help_text": "Service to report errors to",
             "options": ["Sentry", "LogRocket", "Datadog", "Console Only"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-FE-005",
        "title": "Compound Component Pattern",
        "description": "Design a compound component family with implicit state sharing via Context.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Design a compound component family for {{component_family}}.\n\n"
            "Shared internal state: {{shared_state}}\n\n"
            "API usage example:\n{{api_usage_example}}\n\n"
            "Requirements:\n"
            "- Root component owns state via Context\n"
            "- Sub-components consume context with typed hook\n"
            "- Attach sub-components as static properties on root\n"
            "- Full TypeScript"
        ),
        "tags": ["react", "compound-component", "pattern"], "prompt_framework": "APE",
        "subcategory": "patterns", "use_cases": ["tabs", "accordion", "select", "dialog"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Family Name", "placeholder": "e.g. Tabs",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Root component name", "options": [], "order": 0},
            {"label": "Shared Internal State", "placeholder": "activeTab: string; onChange: (tab: string) => void",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "State shared between sub-components", "options": [], "order": 1},
            {"label": "API Usage Example", "placeholder": "<Tabs>\n  <Tabs.List>...</Tabs.List>\n  <Tabs.Panel>...</Tabs.Panel>\n</Tabs>",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "JSX showing intended usage", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-FE-006",
        "title": "Higher-Order Component (HOC) Generator",
        "description": "Generate a typed HOC that injects props into a wrapped component.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Create a Higher-Order Component named {{hoc_name}} that wraps {{wrapped_component}}.\n\n"
            "Props injected by the HOC: {{injected_props}}\n\n"
            "Use case: {{use_case}}\n\n"
            "Requirements:\n"
            "- Preserve wrapped component display name\n"
            "- Use generics to pass through all original props\n"
            "- Export both HOC and wrapped version\n"
            "- Add forwardRef support if needed"
        ),
        "tags": ["react", "hoc", "typescript", "pattern"], "prompt_framework": "CO-STAR",
        "subcategory": "patterns", "use_cases": ["auth gating", "feature flags", "analytics"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "HOC Name", "placeholder": "e.g. withAuth",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "camelCase, prefix with 'with'", "options": [], "order": 0},
            {"label": "Wrapped Component", "placeholder": "e.g. Dashboard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "The component being wrapped", "options": [], "order": 1},
            {"label": "Injected Props", "placeholder": "currentUser: User; permissions: string[]",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Props the HOC will inject", "options": [], "order": 2},
            {"label": "Use Case", "placeholder": "Redirect to login if user is not authenticated",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Why this HOC exists", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-FE-007",
        "title": "React Performance Memoization Audit",
        "description": "Audit a component for unnecessary re-renders and apply useMemo/useCallback/React.memo fixes.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Audit this React component for performance issues:\n\n"
            "Component code:\n{{component_code}}\n\n"
            "Observed problem: {{performance_issue}}\n\n"
            "Rendering frequency: {{rendering_frequency}}\n\n"
            "Tasks:\n"
            "1. Identify all unnecessary re-render causes\n"
            "2. Apply React.memo, useMemo, useCallback where appropriate\n"
            "3. Explain each optimization decision\n"
            "4. Show before/after render count estimate"
        ),
        "tags": ["react", "performance", "memo", "optimization"], "prompt_framework": "STAR",
        "subcategory": "performance", "use_cases": ["render optimization", "profiling"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Code", "placeholder": "Paste your React component here",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "The component to audit", "options": [], "order": 0},
            {"label": "Observed Performance Issue", "placeholder": "Describe the lag or excessive renders you see",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Symptom description", "options": [], "order": 1},
            {"label": "Rendering Frequency", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "On state change",
             "help_text": "How often does this component render?",
             "options": ["Every keystroke", "On state change", "On parent re-render", "On route change"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-FE-008",
        "title": "Form with React Hook Form + Zod",
        "description": "Build a type-safe form using React Hook Form and Zod schema validation.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Build a form named {{form_name}} using React Hook Form + Zod.\n\n"
            "Form fields: {{form_fields}}\n\n"
            "Validation rules: {{validation_rules}}\n\n"
            "On submit action: {{submit_action}}\n\n"
            "Requirements:\n"
            "- Define Zod schema first, infer TypeScript type from it\n"
            "- Use zodResolver in useForm\n"
            "- Show inline error messages per field\n"
            "- Disable submit button while submitting"
        ),
        "tags": ["react", "form", "zod", "validation", "rhf"], "prompt_framework": "CO-STAR",
        "subcategory": "forms", "use_cases": ["login", "signup", "settings", "CRUD forms"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Form Name", "placeholder": "e.g. CreateProjectForm",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase", "options": [], "order": 0},
            {"label": "Form Fields", "placeholder": "name: string, email: string, role: admin|user",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "List each field and its type", "options": [], "order": 1},
            {"label": "Validation Rules", "placeholder": "name: min 2 chars, email: valid email, role: required",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Zod constraints per field", "options": [], "order": 2},
            {"label": "Submit Action", "placeholder": "e.g. POST /api/projects then redirect to /dashboard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "What happens on valid submission", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-FE-009",
        "title": "Infinite Scroll Component",
        "description": "Build an infinite scroll list using IntersectionObserver with loading states and error handling.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Build an infinite scroll component for {{data_source}}.\n\n"
            "Item component: {{item_component}}\n"
            "Page size: {{page_size}} items per page\n"
            "Loading strategy: {{loading_strategy}}\n\n"
            "Requirements:\n"
            "- Sentinel element triggers next page fetch\n"
            "- Skeleton loaders while fetching\n"
            "- End-of-list message when no more data\n"
            "- Error state with retry option\n"
            "- TypeScript generics for item type"
        ),
        "tags": ["react", "infinite-scroll", "intersection-observer", "ux"], "prompt_framework": "CO-STAR",
        "subcategory": "data-display", "use_cases": ["feed", "product list", "search results"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Data Source", "placeholder": "e.g. /api/posts or usePostsQuery",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "API endpoint or hook name", "options": [], "order": 0},
            {"label": "Item Component", "placeholder": "e.g. PostCard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Component that renders one item", "options": [], "order": 1},
            {"label": "Page Size", "placeholder": "20",
             "field_type": "number", "is_required": True, "default_value": "20",
             "help_text": "Items to fetch per page", "options": [], "order": 2},
            {"label": "Loading Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Intersection Observer",
             "help_text": "How to trigger loading more",
             "options": ["Intersection Observer", "Scroll Event", "Manual Load More Button"], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # NEXT.JS & REACT  (INFL-NX-001 … INFL-NX-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-NX-001",
        "title": "Next.js App Router Page Scaffold",
        "description": "Scaffold a complete Next.js 14 App Router page with data fetching, loading, and error segments.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Scaffold a Next.js App Router page at route {{page_route}}.\n\n"
            "Page purpose: {{page_purpose}}\n\n"
            "Data fetching: {{data_fetching}}\n"
            "Auth required: {{auth_required}}\n\n"
            "Generate:\n"
            "- page.tsx (Server Component)\n"
            "- loading.tsx (Suspense fallback)\n"
            "- error.tsx (Error boundary)\n"
            "- layout.tsx if needed\n"
            "- Full TypeScript with proper Next.js PageProps types"
        ),
        "tags": ["nextjs", "app-router", "typescript", "server-component"], "prompt_framework": "CO-STAR",
        "subcategory": "routing", "use_cases": ["new page", "dashboard", "landing"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Page Route", "placeholder": "e.g. /dashboard/projects/[id]",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "App Router file-based route path", "options": [], "order": 0},
            {"label": "Page Purpose", "placeholder": "Display project details and allow inline editing",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What this page does", "options": [], "order": 1},
            {"label": "Data Fetching Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Server Component fetch",
             "help_text": "How data is fetched",
             "options": ["Server Component fetch", "Static Generation (SSG)", "ISR with revalidate", "Client-side SWR"], "order": 2},
            {"label": "Auth Required", "placeholder": "",
             "field_type": "radio", "is_required": True, "default_value": "Yes",
             "help_text": "Does this page require authentication?",
             "options": ["Yes", "No"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-NX-002",
        "title": "Next.js Server Component with Data Fetch",
        "description": "Create a Next.js Server Component that fetches data with proper caching and TypeScript.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Create a Next.js Server Component named {{component_name}}.\n\n"
            "Data endpoint: {{data_endpoint}}\n"
            "Data shape (TypeScript):\n{{data_shape}}\n\n"
            "Cache strategy: {{cache_strategy}}\n\n"
            "Requirements:\n"
            "- async/await with proper error handling\n"
            "- TypeScript interfaces for fetched data\n"
            "- Proper Next.js fetch cache config\n"
            "- Suspense-compatible (no client-side loading state)"
        ),
        "tags": ["nextjs", "server-component", "data-fetching", "typescript"], "prompt_framework": "CO-STAR",
        "subcategory": "server-components",
        "use_cases": ["data display", "server-side rendering"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Name", "placeholder": "e.g. ProjectList",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase name", "options": [], "order": 0},
            {"label": "Data Endpoint", "placeholder": "https://api.example.com/projects",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "API URL or server action", "options": [], "order": 1},
            {"label": "Data Shape (TypeScript)", "placeholder": "{ id: string; name: string; status: string }[]",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "TypeScript type of the fetched data", "options": [], "order": 2},
            {"label": "Cache Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "force-cache",
             "help_text": "Next.js fetch cache option",
             "options": ["force-cache", "no-store", "revalidate 60", "revalidate 3600"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-NX-003",
        "title": "Next.js API Route Handler",
        "description": "Create a type-safe Next.js App Router API route handler with request validation and error responses.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Create a Next.js App Router API route at {{route_path}}.\n\n"
            "HTTP method: {{http_method}}\n\n"
            "Request body schema:\n{{request_body_schema}}\n\n"
            "Success response schema:\n{{response_schema}}\n\n"
            "Requirements:\n"
            "- Use NextRequest/NextResponse types\n"
            "- Validate request body with Zod\n"
            "- Return typed JSON responses\n"
            "- Handle and return structured errors (400, 401, 404, 500)"
        ),
        "tags": ["nextjs", "api-route", "typescript", "zod"], "prompt_framework": "CO-STAR",
        "subcategory": "api-routes",
        "use_cases": ["REST endpoint", "form handler", "webhook receiver"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Route Path", "placeholder": "e.g. /api/projects",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "File-based route path", "options": [], "order": 0},
            {"label": "HTTP Method", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "POST",
             "help_text": "Primary HTTP method",
             "options": ["GET", "POST", "PUT", "PATCH", "DELETE"], "order": 1},
            {"label": "Request Body Schema", "placeholder": "{ name: string; description?: string }",
             "field_type": "textarea", "is_required": False, "default_value": "",
             "help_text": "Expected request body type", "options": [], "order": 2},
            {"label": "Response Schema", "placeholder": "{ id: string; name: string; createdAt: string }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Success response type", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-NX-004",
        "title": "Next.js Middleware for Auth & Routing",
        "description": "Write Next.js middleware to protect routes, redirect unauthenticated users, and set response headers.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Write Next.js middleware to protect routes.\n\n"
            "Protected path patterns: {{protected_paths}}\n\n"
            "Auth strategy: {{auth_strategy}}\n\n"
            "Redirect URL for unauthenticated users: {{redirect_url}}\n\n"
            "Requirements:\n"
            "- Use NextResponse.redirect and NextResponse.next\n"
            "- Match only specified patterns in config.matcher\n"
            "- Add security headers (X-Frame-Options, CSP) on all responses\n"
            "- Log auth failures with structured data"
        ),
        "tags": ["nextjs", "middleware", "auth", "security"], "prompt_framework": "CO-STAR",
        "subcategory": "middleware",
        "use_cases": ["auth gating", "RBAC", "header injection"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Protected Path Patterns", "placeholder": "/dashboard/:path*, /admin/:path*",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Paths to protect (one per line)", "options": [], "order": 0},
            {"label": "Auth Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "JWT Cookie",
             "help_text": "How to verify authentication",
             "options": ["JWT Cookie", "Session Cookie", "Bearer Token Header", "Custom"], "order": 1},
            {"label": "Redirect URL", "placeholder": "/login",
             "field_type": "text", "is_required": True, "default_value": "/login",
             "help_text": "Where to send unauthenticated users", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-NX-005",
        "title": "Next.js Server Action Form",
        "description": "Implement a Next.js Server Action with form binding, validation, optimistic updates, and error handling.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Implement a Next.js Server Action named {{action_name}}.\n\n"
            "Form fields: {{form_fields}}\n\n"
            "Validation library: {{validation_library}}\n\n"
            "On success redirect to: {{success_redirect}}\n\n"
            "Requirements:\n"
            "- 'use server' directive\n"
            "- Zod/Yup validation before DB operations\n"
            "- useFormState for error propagation to client\n"
            "- useFormStatus to disable button during submission\n"
            "- revalidatePath after mutation"
        ),
        "tags": ["nextjs", "server-action", "form", "typescript"], "prompt_framework": "CO-STAR",
        "subcategory": "server-actions",
        "use_cases": ["create/update/delete forms", "progressive enhancement"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Action Name", "placeholder": "e.g. createProject",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "camelCase server action function name", "options": [], "order": 0},
            {"label": "Form Fields", "placeholder": "name: string, description: string, isPublic: boolean",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Fields in the form", "options": [], "order": 1},
            {"label": "Validation Library", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Zod",
             "help_text": "Schema validation library",
             "options": ["Zod", "Yup", "Valibot", "Custom"], "order": 2},
            {"label": "Success Redirect", "placeholder": "/dashboard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Path to redirect after success", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-NX-006",
        "title": "Next.js Metadata & SEO Template",
        "description": "Generate Next.js 14 static and dynamic metadata with Open Graph, Twitter cards, and canonical URLs.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Generate Next.js metadata for the page: {{page_name}}.\n\n"
            "Page description: {{page_description}}\n"
            "OG image path: {{og_image_path}}\n"
            "Canonical URL: {{canonical_url}}\n\n"
            "Generate:\n"
            "1. Static `metadata` export for layout/root\n"
            "2. Dynamic `generateMetadata` for dynamic routes\n"
            "3. Open Graph tags (title, description, image, type)\n"
            "4. Twitter card tags\n"
            "5. robots and canonical link"
        ),
        "tags": ["nextjs", "seo", "metadata", "og-tags"], "prompt_framework": "CO-STAR",
        "subcategory": "seo",
        "use_cases": ["SEO optimization", "social sharing", "structured data"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Page Name", "placeholder": "e.g. Project Dashboard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Human-readable page name", "options": [], "order": 0},
            {"label": "Page Description", "placeholder": "Manage and track all your projects in one place.",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "150–160 characters for best SEO", "options": [], "order": 1},
            {"label": "OG Image Path", "placeholder": "/og/dashboard.png",
             "field_type": "text", "is_required": False, "default_value": "/og/default.png",
             "help_text": "Relative path to Open Graph image (1200×630px)", "options": [], "order": 2},
            {"label": "Canonical URL", "placeholder": "https://yourapp.com/dashboard",
             "field_type": "text", "is_required": False, "default_value": "",
             "help_text": "Full canonical URL for this page", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-NX-007",
        "title": "Next.js Image Optimization Component",
        "description": "Create a wrapper around next/image with blur placeholder, responsive sizes, and fallback handling.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Create a Next.js optimized image component.\n\n"
            "Image usage context: {{image_usage}}\n"
            "Dimensions: {{image_dimensions}}\n"
            "Loading priority: {{loading_strategy}}\n"
            "Placeholder type: {{placeholder_type}}\n\n"
            "Requirements:\n"
            "- Wrap next/image with sensible defaults\n"
            "- Accept all next/image props via spread\n"
            "- Handle src error with fallback image\n"
            "- Generate correct sizes prop for responsive layouts"
        ),
        "tags": ["nextjs", "images", "performance", "optimization"], "prompt_framework": "CO-STAR",
        "subcategory": "media",
        "use_cases": ["hero images", "avatars", "product photos", "blog covers"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Image Usage Context", "placeholder": "Full-width hero banner above the fold",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Where and how the image is used", "options": [], "order": 0},
            {"label": "Image Dimensions", "placeholder": "1200x630",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Width x Height in px", "options": [], "order": 1},
            {"label": "Loading Priority", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "lazy",
             "help_text": "next/image priority setting",
             "options": ["lazy", "eager", "priority (LCP image)"], "order": 2},
            {"label": "Placeholder Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "blur",
             "help_text": "Placeholder shown while loading",
             "options": ["blur", "empty", "none"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-NX-008",
        "title": "Next.js ISR + On-Demand Revalidation",
        "description": "Configure Incremental Static Regeneration with on-demand revalidation via a webhook-triggered API route.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Configure ISR for Next.js page at route {{page_route}}.\n\n"
            "Data source: {{data_source}}\n"
            "Revalidation interval: {{revalidate_interval}} seconds\n\n"
            "On-demand revalidation trigger:\n{{on_demand_trigger}}\n\n"
            "Generate:\n"
            "1. Page with `export const revalidate = {{revalidate_interval}}`\n"
            "2. /api/revalidate route handler with secret token check\n"
            "3. Webhook payload handler to call revalidatePath\n"
            "4. Error handling for failed revalidations"
        ),
        "tags": ["nextjs", "isr", "revalidation", "performance"], "prompt_framework": "CO-STAR",
        "subcategory": "caching",
        "use_cases": ["blog", "e-commerce", "marketing site"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Page Route", "placeholder": "/blog/[slug]",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Next.js page route", "options": [], "order": 0},
            {"label": "Data Source", "placeholder": "CMS API at https://cms.example.com/posts",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Where the page data comes from", "options": [], "order": 1},
            {"label": "Revalidate Interval (seconds)", "placeholder": "3600",
             "field_type": "number", "is_required": True, "default_value": "3600",
             "help_text": "Background revalidation frequency", "options": [], "order": 2},
            {"label": "On-Demand Trigger", "placeholder": "CMS publishes event sends POST to /api/revalidate",
             "field_type": "textarea", "is_required": False, "default_value": "",
             "help_text": "What triggers instant revalidation", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-NX-009",
        "title": "Next.js Dynamic Route + generateStaticParams",
        "description": "Scaffold a Next.js dynamic route with generateStaticParams for static pre-rendering and typed params.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Create a Next.js dynamic route for {{dynamic_segment}}.\n\n"
            "Data source for params: {{data_source}}\n\n"
            "Fallback behavior: {{fallback_behavior}}\n\n"
            "Requirements:\n"
            "- generateStaticParams fetches all possible params at build time\n"
            "- page.tsx uses typed `params` prop\n"
            "- notFound() for missing slugs\n"
            "- TypeScript PageProps with params and searchParams types"
        ),
        "tags": ["nextjs", "dynamic-routes", "ssg", "typescript"], "prompt_framework": "CO-STAR",
        "subcategory": "routing",
        "use_cases": ["blog posts", "product pages", "user profiles"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Dynamic Segment", "placeholder": "e.g. [slug] for /posts/[slug]",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Next.js dynamic segment name", "options": [], "order": 0},
            {"label": "Data Source for Params", "placeholder": "CMS API returning all slugs",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Where to fetch all possible param values", "options": [], "order": 1},
            {"label": "Fallback Behavior", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "blocking",
             "help_text": "What happens for params not generated at build time",
             "options": ["blocking", "force-dynamic", "return notFound"], "order": 2},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # TYPESCRIPT  (INFL-TS-001 … INFL-TS-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-TS-001",
        "title": "Generic Utility Type Creator",
        "description": "Design a reusable TypeScript generic utility type with documentation and usage examples.",
        "category_slug": "typescript",
        "template_content": (
            "Create a TypeScript generic utility type named {{type_name}}.\n\n"
            "Base type this operates on: {{base_type}}\n\n"
            "Transformation goal: {{transformation_goal}}\n\n"
            "Usage example: {{usage_example}}\n\n"
            "Requirements:\n"
            "- Explain the type in a JSDoc comment\n"
            "- Show 3 concrete usage examples\n"
            "- Compare to any similar built-in utility types\n"
            "- Note any edge cases or limitations"
        ),
        "tags": ["typescript", "generics", "utility-types"], "prompt_framework": "APE",
        "subcategory": "type-system",
        "use_cases": ["type library", "DRY typing", "strict API contracts"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Type Name", "placeholder": "e.g. DeepReadonly",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase utility type name", "options": [], "order": 0},
            {"label": "Base Type", "placeholder": "T extends object",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Generic constraint", "options": [], "order": 1},
            {"label": "Transformation Goal", "placeholder": "Make all nested properties readonly",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What this type does", "options": [], "order": 2},
            {"label": "Usage Example", "placeholder": "type ImmutableUser = DeepReadonly<User>",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Concrete usage", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-TS-002",
        "title": "Discriminated Union Pattern",
        "description": "Define a TypeScript discriminated union with exhaustive switch handling and type guards.",
        "category_slug": "typescript",
        "template_content": (
            "Create a TypeScript discriminated union named {{union_name}}.\n\n"
            "Variants and their unique fields:\n{{variants}}\n\n"
            "Discriminant field: {{discriminant_field}}\n\n"
            "Consumer usage example:\n{{consumer_example}}\n\n"
            "Requirements:\n"
            "- Each variant is a distinct interface with the discriminant\n"
            "- Exhaustive switch with never check\n"
            "- Type guard function for each variant\n"
            "- JSDoc per variant"
        ),
        "tags": ["typescript", "discriminated-union", "type-safety"], "prompt_framework": "CO-STAR",
        "subcategory": "type-system",
        "use_cases": ["state machines", "API response types", "event handling"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Union Name", "placeholder": "e.g. PaymentStatus",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase union name", "options": [], "order": 0},
            {"label": "Variants", "placeholder": "Pending: {}, Success: { transactionId: string }, Failed: { reason: string }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Each variant and its unique fields", "options": [], "order": 1},
            {"label": "Discriminant Field", "placeholder": "status",
             "field_type": "text", "is_required": True, "default_value": "type",
             "help_text": "The string literal field used to discriminate", "options": [], "order": 2},
            {"label": "Consumer Usage Example", "placeholder": "switch(payment.status) { case 'success': ... }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "How this union will be consumed", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-TS-003",
        "title": "Mapped Type Generator",
        "description": "Create a TypeScript mapped type that transforms an existing type systematically.",
        "category_slug": "typescript",
        "template_content": (
            "Create a TypeScript mapped type based on {{source_type}}.\n\n"
            "Transformation to apply: {{transformation}}\n\n"
            "Result type name: {{result_type_name}}\n\n"
            "Requirements:\n"
            "- Show the full mapped type definition\n"
            "- Explain key remapping if used\n"
            "- Show +/- modifier usage if relevant\n"
            "- Provide a concrete before/after example"
        ),
        "tags": ["typescript", "mapped-types", "type-system"], "prompt_framework": "APE",
        "subcategory": "type-system",
        "use_cases": ["form state typing", "API transformations", "ORM typing"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Source Type", "placeholder": "e.g. User interface with all fields",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "The type to map over", "options": [], "order": 0},
            {"label": "Transformation", "placeholder": "Make all fields optional and wrap values in Promise",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "How to transform each property", "options": [], "order": 1},
            {"label": "Result Type Name", "placeholder": "AsyncPartial",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Name for the new mapped type", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-TS-004",
        "title": "Zod Schema with TypeScript Inference",
        "description": "Build a Zod validation schema with inferred TypeScript type, transforms, and nested object support.",
        "category_slug": "typescript",
        "template_content": (
            "Create a Zod schema named {{schema_name}}.\n\n"
            "Fields to validate:\n{{fields_description}}\n\n"
            "Validation constraints:\n{{validation_constraints}}\n\n"
            "Requirements:\n"
            "- Define schema with z.object()\n"
            "- Use z.infer<> to export TypeScript type\n"
            "- Add .transform() where data normalization is needed\n"
            "- Add .refine() for cross-field validation\n"
            "- Export both schema and inferred type"
        ),
        "tags": ["typescript", "zod", "validation", "schema"], "prompt_framework": "CO-STAR",
        "subcategory": "validation",
        "use_cases": ["form validation", "API request parsing", "env validation"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Schema Name", "placeholder": "e.g. CreateUserSchema",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase schema name", "options": [], "order": 0},
            {"label": "Fields Description", "placeholder": "name: string, email: email, age: number > 18",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Each field with its type", "options": [], "order": 1},
            {"label": "Validation Constraints", "placeholder": "name min 2, max 50; email must be unique; confirm password must match password",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Business rules and cross-field constraints", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-TS-005",
        "title": "TypeScript Strict API Response Types",
        "description": "Define typed API response wrappers with success/error discrimination and HTTP status codes.",
        "category_slug": "typescript",
        "template_content": (
            "Define typed API response types for endpoint {{api_endpoint}} ({{http_method}}).\n\n"
            "Success response shape:\n{{success_shape}}\n\n"
            "Error response shape:\n{{error_shape}}\n\n"
            "Requirements:\n"
            "- Create ApiResponse<T> generic wrapper\n"
            "- Discriminated union between success and error\n"
            "- Include HTTP status code in type\n"
            "- Type guard functions isSuccess() and isError()\n"
            "- Export all types for use in client and server"
        ),
        "tags": ["typescript", "api", "response-types", "generics"], "prompt_framework": "CO-STAR",
        "subcategory": "api-types",
        "use_cases": ["client-server contracts", "fetch wrappers", "tRPC-style typing"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "API Endpoint", "placeholder": "POST /api/auth/login",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Method + path", "options": [], "order": 0},
            {"label": "HTTP Method", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "POST",
             "help_text": "HTTP verb",
             "options": ["GET", "POST", "PUT", "PATCH", "DELETE"], "order": 1},
            {"label": "Success Response Shape", "placeholder": "{ token: string; user: { id: string; email: string } }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "TypeScript type for success body", "options": [], "order": 2},
            {"label": "Error Response Shape", "placeholder": "{ code: string; message: string; field?: string }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "TypeScript type for error body", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-TS-006",
        "title": "TypeScript Module Declaration (d.ts)",
        "description": "Write a .d.ts ambient module declaration for an untyped third-party library.",
        "category_slug": "typescript",
        "template_content": (
            "Write a TypeScript ambient module declaration for {{module_name}}.\n\n"
            "Exported types and functions:\n{{exported_types}}\n\n"
            "Usage context: {{usage_context}}\n\n"
            "Requirements:\n"
            "- `declare module '{{module_name}}'` wrapper\n"
            "- Typed exports for all public API surface\n"
            "- Use `export default` and named exports as appropriate\n"
            "- Add JSDoc to each declaration\n"
            "- Place in src/types/{{module_name}}.d.ts"
        ),
        "tags": ["typescript", "declarations", "d.ts", "types"], "prompt_framework": "APE",
        "subcategory": "declarations",
        "use_cases": ["untyped libraries", "vendor type stubs", "legacy code"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Module Name", "placeholder": "e.g. some-untyped-lib",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "npm package name", "options": [], "order": 0},
            {"label": "Exported Types and Functions", "placeholder": "export function parse(input: string): Result\nexport interface Result { ... }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Public API to declare", "options": [], "order": 1},
            {"label": "Usage Context", "placeholder": "Used for CSV parsing in data import module",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "How this module is used in the project", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-TS-007",
        "title": "Conditional Type Pattern",
        "description": "Implement a TypeScript conditional type with infer, distributive behavior, and test cases.",
        "category_slug": "typescript",
        "template_content": (
            "Implement a TypeScript conditional type named {{type_name}}.\n\n"
            "Condition: {{condition}}\n"
            "True branch result: {{true_branch}}\n"
            "False branch result: {{false_branch}}\n\n"
            "Requirements:\n"
            "- Show distributive behavior over union types\n"
            "- Use `infer` keyword if extracting inner type\n"
            "- Write 5 test cases using type-level assertions\n"
            "- Note any recursion depth limits"
        ),
        "tags": ["typescript", "conditional-types", "infer"], "prompt_framework": "APE",
        "subcategory": "type-system",
        "use_cases": ["type inference", "conditional APIs", "type narrowing"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Type Name", "placeholder": "e.g. UnpackPromise",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "PascalCase name for the conditional type", "options": [], "order": 0},
            {"label": "Condition", "placeholder": "T extends Promise<infer U>",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "The type-level condition to check", "options": [], "order": 1},
            {"label": "True Branch Result", "placeholder": "U (the inner type)",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Type returned when condition is true", "options": [], "order": 2},
            {"label": "False Branch Result", "placeholder": "T (unchanged)",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Type returned when condition is false", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-TS-008",
        "title": "TypeScript tsconfig Strictness Upgrade",
        "description": "Plan and execute a gradual tsconfig strictness upgrade with per-flag migration checklist.",
        "category_slug": "typescript",
        "template_content": (
            "Plan a TypeScript strictness upgrade for a {{codebase_size}} codebase.\n\n"
            "Current tsconfig:\n{{current_tsconfig}}\n\n"
            "Target strictness level: {{strictness_target}}\n\n"
            "Generate:\n"
            "1. Ordered list of flags to enable (safest first)\n"
            "2. Most common error patterns per flag\n"
            "3. Automated codemods or ESLint rules to fix bulk errors\n"
            "4. Estimated error count per flag based on codebase size\n"
            "5. Rollback plan per flag"
        ),
        "tags": ["typescript", "tsconfig", "strict", "migration"], "prompt_framework": "STAR",
        "subcategory": "configuration",
        "use_cases": ["legacy migration", "type safety improvement", "strictness adoption"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Current tsconfig", "placeholder": "Paste your tsconfig.json compilerOptions",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Current compiler options", "options": [], "order": 0},
            {"label": "Codebase Size", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Medium (10k–50k LOC)",
             "help_text": "Approximate lines of TypeScript",
             "options": ["Small (<10k LOC)", "Medium (10k–50k LOC)", "Large (>50k LOC)"], "order": 1},
            {"label": "Strictness Target", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "strict",
             "help_text": "Target compiler strictness",
             "options": ["strict", "noImplicitAny only", "strictNullChecks only", "All flags enabled"], "order": 2},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # CSS & STYLING  (INFL-CSS-001 … INFL-CSS-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-CSS-001",
        "title": "Tailwind Component Design Token System",
        "description": "Design a Tailwind CSS design token extension for a component with semantic color and spacing tokens.",
        "category_slug": "css-styling",
        "template_content": (
            "Design Tailwind CSS tokens for {{component_name}}.\n\n"
            "Design requirements: {{design_requirements}}\n"
            "Color palette: {{color_palette}}\n\n"
            "Generate:\n"
            "1. tailwind.config.ts theme.extend with semantic color tokens\n"
            "2. Spacing, border-radius, and shadow tokens\n"
            "3. Component-specific utility class composition\n"
            "4. Dark mode variants for all tokens\n"
            "5. CSS custom properties fallback in globals.css"
        ),
        "tags": ["tailwind", "design-tokens", "css", "theming"], "prompt_framework": "CO-STAR",
        "subcategory": "design-system",
        "use_cases": ["design system", "component library", "white-labeling"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Name", "placeholder": "e.g. Button or Card",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Component to create tokens for", "options": [], "order": 0},
            {"label": "Design Requirements", "placeholder": "Brand colors: indigo/purple. Rounded corners. Subtle shadows.",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Visual design requirements", "options": [], "order": 1},
            {"label": "Color Palette", "placeholder": "Primary: #6366F1, Secondary: #8B5CF6, Neutral: #6B7280",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Brand hex colors", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-CSS-002",
        "title": "CSS Grid Layout Generator",
        "description": "Generate a named CSS Grid layout with responsive column/row definitions and area placement.",
        "category_slug": "css-styling",
        "template_content": (
            "Generate a CSS Grid layout named {{layout_name}}.\n\n"
            "Grid structure description: {{grid_structure}}\n"
            "Gap size: {{gap_size}}\n"
            "Responsive behavior: {{responsive_behavior}}\n\n"
            "Requirements:\n"
            "- Use grid-template-areas with named regions\n"
            "- Define grid-template-columns with minmax/fr units\n"
            "- Include responsive breakpoints that collapse to single column\n"
            "- Add subgrid variant for nested alignment\n"
            "- Comment each area's purpose"
        ),
        "tags": ["css", "grid", "layout", "responsive"], "prompt_framework": "CO-STAR",
        "subcategory": "layout",
        "use_cases": ["dashboard layout", "magazine layout", "complex page structure"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Layout Name", "placeholder": "e.g. DashboardLayout",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "CSS class name for this layout", "options": [], "order": 0},
            {"label": "Grid Structure", "placeholder": "Sidebar left (240px), main content area, right panel (300px)",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Describe columns, rows, and areas", "options": [], "order": 1},
            {"label": "Gap Size", "placeholder": "1.5rem",
             "field_type": "text", "is_required": False, "default_value": "1rem",
             "help_text": "CSS gap value", "options": [], "order": 2},
            {"label": "Responsive Behavior", "placeholder": "Sidebar collapses below 768px, panel hides below 1024px",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Breakpoint behavior description", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-CSS-003",
        "title": "Dark Mode Implementation (Tailwind + CSS Variables)",
        "description": "Implement dark mode using Tailwind class strategy and CSS custom properties with smooth transitions.",
        "category_slug": "css-styling",
        "template_content": (
            "Implement dark mode for {{component_name}}.\n\n"
            "Light theme tokens: {{light_tokens}}\n"
            "Dark theme tokens: {{dark_tokens}}\n"
            "Toggle approach: {{toggle_approach}}\n\n"
            "Generate:\n"
            "1. CSS custom properties for both themes in :root and .dark\n"
            "2. Tailwind config darkMode: '{{toggle_approach}}'\n"
            "3. React ThemeProvider component with localStorage persistence\n"
            "4. useTheme hook returning current theme + toggle function\n"
            "5. CSS transition for theme switch (color, background-color)"
        ),
        "tags": ["css", "dark-mode", "tailwind", "theming"], "prompt_framework": "CO-STAR",
        "subcategory": "theming",
        "use_cases": ["dark mode feature", "theme toggle", "system preference support"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component / Scope Name", "placeholder": "e.g. App or Dashboard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Component or app scope", "options": [], "order": 0},
            {"label": "Light Theme Tokens", "placeholder": "--bg: #ffffff; --text: #111827; --border: #E5E7EB",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "CSS custom properties for light theme", "options": [], "order": 1},
            {"label": "Dark Theme Tokens", "placeholder": "--bg: #0F172A; --text: #F8FAFC; --border: #1E293B",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "CSS custom properties for dark theme", "options": [], "order": 2},
            {"label": "Toggle Approach", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "class",
             "help_text": "How dark mode is activated",
             "options": ["class", "media", "data-attribute"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-CSS-004",
        "title": "CSS Animation & Keyframe Builder",
        "description": "Create performant CSS keyframe animations with GPU-accelerated properties and reduced-motion support.",
        "category_slug": "css-styling",
        "template_content": (
            "Create a CSS animation named {{animation_name}} for {{element_description}}.\n\n"
            "Animation goal: {{animation_goal}}\n"
            "Duration: {{duration}}\n"
            "Easing: {{easing}}\n\n"
            "Requirements:\n"
            "- Use only transform and opacity for GPU acceleration\n"
            "- @keyframes definition with intermediate stops\n"
            "- @media (prefers-reduced-motion: reduce) override\n"
            "- Tailwind variant if applicable\n"
            "- Document fill-mode and iteration-count choices"
        ),
        "tags": ["css", "animation", "keyframes", "performance"], "prompt_framework": "CO-STAR",
        "subcategory": "animation",
        "use_cases": ["entrance animations", "loading states", "micro-interactions"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Animation Name", "placeholder": "e.g. slide-in-right",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "kebab-case animation name", "options": [], "order": 0},
            {"label": "Element Description", "placeholder": "e.g. modal dialog appearing from bottom",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "What is being animated", "options": [], "order": 1},
            {"label": "Animation Goal", "placeholder": "Fade in while sliding up 20px",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Start and end visual states", "options": [], "order": 2},
            {"label": "Duration", "placeholder": "300ms",
             "field_type": "text", "is_required": False, "default_value": "300ms",
             "help_text": "Animation duration", "options": [], "order": 3},
            {"label": "Easing", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "ease-out",
             "help_text": "Timing function",
             "options": ["ease", "ease-in", "ease-out", "ease-in-out", "linear", "cubic-bezier(spring)"], "order": 4},
        ],
    },
    {
        "external_id": "INFL-CSS-005",
        "title": "Responsive Breakpoint Strategy",
        "description": "Define a responsive breakpoint strategy with container queries or media queries and component adaptation rules.",
        "category_slug": "css-styling",
        "template_content": (
            "Design a responsive strategy for {{component_affected}} using {{design_system}}.\n\n"
            "Breakpoints and layout changes:\n{{breakpoints}}\n\n"
            "Requirements:\n"
            "- Define breakpoint tokens with semantic names (mobile/tablet/desktop/wide)\n"
            "- Show media query or container query syntax for each breakpoint\n"
            "- List which CSS properties change at each breakpoint\n"
            "- Document the mobile-first vs desktop-first approach\n"
            "- Include Tailwind utility classes if applicable"
        ),
        "tags": ["css", "responsive", "breakpoints", "tailwind"], "prompt_framework": "CO-STAR",
        "subcategory": "responsive-design",
        "use_cases": ["responsive layouts", "adaptive components"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Affected", "placeholder": "e.g. NavigationBar or ProductGrid",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Which component to make responsive", "options": [], "order": 0},
            {"label": "Design System", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Tailwind CSS",
             "help_text": "CSS framework or methodology",
             "options": ["Tailwind CSS", "Bootstrap", "Custom Media Queries", "CSS Container Queries"], "order": 1},
            {"label": "Breakpoints and Layout Changes", "placeholder": "mobile: stacked; tablet: 2-col; desktop: sidebar+content",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Layout changes at each breakpoint", "options": [], "order": 2},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # WEB PERFORMANCE  (INFL-PERF-001 … INFL-PERF-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-PERF-001",
        "title": "Core Web Vitals Audit & Fix Plan",
        "description": "Analyze Core Web Vitals metrics and generate a prioritized improvement plan with code fixes.",
        "category_slug": "web-performance",
        "template_content": (
            "Audit Core Web Vitals for this page.\n\n"
            "Page URL: {{page_url}}\n"
            "Current LCP: {{current_lcp}}\n"
            "Current CLS: {{current_cls}}\n"
            "Current FID/INP: {{current_fid}}\n\n"
            "Generate:\n"
            "1. Root cause analysis for each failing metric\n"
            "2. Prioritized fix list (quick wins first)\n"
            "3. Code snippets for top 3 fixes\n"
            "4. Expected metric improvement per fix\n"
            "5. Monitoring strategy with web-vitals.js"
        ),
        "tags": ["performance", "cwv", "lcp", "cls", "inp"], "prompt_framework": "STAR",
        "subcategory": "core-web-vitals",
        "use_cases": ["SEO optimization", "UX improvement", "PageSpeed score"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Page URL", "placeholder": "https://yourapp.com/products",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "The page being audited", "options": [], "order": 0},
            {"label": "Current LCP (ms)", "placeholder": "e.g. 4200",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Largest Contentful Paint in ms", "options": [], "order": 1},
            {"label": "Current CLS Score", "placeholder": "e.g. 0.18",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Cumulative Layout Shift score (0–1)", "options": [], "order": 2},
            {"label": "Current FID/INP (ms)", "placeholder": "e.g. 320",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Interaction latency in ms", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-PERF-002",
        "title": "Bundle Size Analysis & Code Splitting Plan",
        "description": "Analyze JavaScript bundle composition and generate a code-splitting and tree-shaking strategy.",
        "category_slug": "web-performance",
        "template_content": (
            "Analyze and optimize the JavaScript bundle for {{framework}}.\n\n"
            "Current total bundle size: {{current_bundle_size}}\n\n"
            "Heavy dependencies identified:\n{{heavy_dependencies}}\n\n"
            "Splitting strategy: {{splitting_strategy}}\n\n"
            "Generate:\n"
            "1. Dynamic import() refactors for heavy routes/components\n"
            "2. Tree-shaking fixes (named vs default imports)\n"
            "3. next/bundle-analyzer or rollup-plugin-visualizer setup\n"
            "4. Expected bundle size reduction estimate\n"
            "5. webpack/Turbopack/Vite config optimizations"
        ),
        "tags": ["performance", "bundle", "code-splitting", "webpack"], "prompt_framework": "STAR",
        "subcategory": "bundling",
        "use_cases": ["initial load time", "TTI optimization", "lazy loading"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Framework", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Next.js",
             "help_text": "Build framework",
             "options": ["Next.js", "React + Vite", "Remix", "Astro"], "order": 0},
            {"label": "Current Bundle Size", "placeholder": "e.g. 1.2MB gzipped",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Total JS bundle size", "options": [], "order": 1},
            {"label": "Heavy Dependencies", "placeholder": "moment.js (67KB), lodash (71KB), chart.js (200KB)",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Large packages identified in bundle analyzer", "options": [], "order": 2},
            {"label": "Splitting Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Route-based",
             "help_text": "Primary code-splitting approach",
             "options": ["Route-based", "Component-based lazy()", "Library-based", "All of the above"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-PERF-003",
        "title": "React Render Performance Audit",
        "description": "Identify and fix unnecessary React re-renders using Profiler data and memoization techniques.",
        "category_slug": "web-performance",
        "template_content": (
            "Audit React render performance for {{component_name}}.\n\n"
            "Component code:\n{{component_code}}\n\n"
            "React Profiler data / observed issue:\n{{profiler_data}}\n\n"
            "Tasks:\n"
            "1. Identify all unnecessary render causes\n"
            "2. Apply React.memo / useMemo / useCallback with justification\n"
            "3. Suggest state colocation or lifting changes\n"
            "4. Show before/after render timeline estimate\n"
            "5. Add React DevTools Profiler annotations"
        ),
        "tags": ["react", "performance", "profiling", "memo"], "prompt_framework": "STAR",
        "subcategory": "react-performance",
        "use_cases": ["render optimization", "large list performance", "form performance"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Name", "placeholder": "e.g. DataTable",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Component to audit", "options": [], "order": 0},
            {"label": "Component Code", "placeholder": "Paste the component source here",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Full component source", "options": [], "order": 1},
            {"label": "Profiler Data / Observed Issue", "placeholder": "Renders 50x per keystroke; commit time 120ms",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "React Profiler output or described symptom", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-PERF-004",
        "title": "Service Worker + Caching Strategy",
        "description": "Design a Service Worker caching strategy with offline support and cache invalidation.",
        "category_slug": "web-performance",
        "template_content": (
            "Design a Service Worker caching strategy for a {{app_type}} application.\n\n"
            "Assets to cache:\n{{assets_to_cache}}\n\n"
            "Cache strategy: {{cache_strategy}}\n\n"
            "Generate:\n"
            "1. Service Worker registration in app root\n"
            "2. install event precaching list\n"
            "3. fetch event handler with {{cache_strategy}} logic\n"
            "4. activate event for cache cleanup\n"
            "5. Workbox config alternative\n"
            "6. Offline fallback page"
        ),
        "tags": ["pwa", "service-worker", "caching", "offline"], "prompt_framework": "CO-STAR",
        "subcategory": "caching",
        "use_cases": ["PWA", "offline support", "performance optimization"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "App Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "SPA",
             "help_text": "Type of web application",
             "options": ["SPA", "PWA", "SSR Next.js", "Static Site"], "order": 0},
            {"label": "Assets to Cache", "placeholder": "HTML shell, CSS, JS bundles, fonts, critical images",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "List of asset types to cache", "options": [], "order": 1},
            {"label": "Cache Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Stale While Revalidate",
             "help_text": "Workbox/custom cache strategy",
             "options": ["Cache First", "Network First", "Stale While Revalidate", "Network Only"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-PERF-005",
        "title": "N+1 Query Detector & Fix",
        "description": "Identify N+1 query patterns in ORM code and apply select_related/prefetch_related or DataLoader fixes.",
        "category_slug": "web-performance",
        "template_content": (
            "Identify and fix N+1 query issues in {{model_name}} queries.\n\n"
            "Query pattern with N+1 issue:\n{{query_pattern}}\n\n"
            "ORM framework: {{orm_framework}}\n\n"
            "Tasks:\n"
            "1. Explain why this code produces N+1 queries\n"
            "2. Rewrite using eager loading / prefetch\n"
            "3. Show SQL query count before and after\n"
            "4. Add Django Debug Toolbar / EXPLAIN ANALYZE guidance\n"
            "5. Suggest indexing if applicable"
        ),
        "tags": ["performance", "database", "n+1", "orm"], "prompt_framework": "STAR",
        "subcategory": "database",
        "use_cases": ["API performance", "database optimization", "ORM best practices"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Model Name", "placeholder": "e.g. Post with User and Comments",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "The model with relationship queries", "options": [], "order": 0},
            {"label": "Query Pattern (Code)", "placeholder": "Paste the ORM query or code block",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Code that has N+1 issue", "options": [], "order": 1},
            {"label": "ORM Framework", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Django ORM",
             "help_text": "Your ORM",
             "options": ["Django ORM", "Prisma", "TypeORM", "Drizzle", "SQLAlchemy"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-PERF-006",
        "title": "Font Loading Performance Strategy",
        "description": "Optimize web font loading with preload, font-display, and self-hosting recommendations.",
        "category_slug": "web-performance",
        "template_content": (
            "Optimize web font loading for {{font_families}}.\n\n"
            "Number of font weights/styles: {{font_count}}\n"
            "Loading strategy: {{loading_strategy}}\n"
            "Fallback fonts: {{fallback_fonts}}\n\n"
            "Generate:\n"
            "1. HTML <link rel='preload'> tags for critical fonts\n"
            "2. @font-face declarations with font-display: {{loading_strategy}}\n"
            "3. CSS font-stack with metric-compatible fallbacks\n"
            "4. next/font or fontaine integration\n"
            "5. FOUT/FOIT/FOFT mitigation strategy"
        ),
        "tags": ["performance", "fonts", "loading", "fout"], "prompt_framework": "CO-STAR",
        "subcategory": "fonts",
        "use_cases": ["font optimization", "CLS reduction", "render performance"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Font Families", "placeholder": "Inter, Fira Code",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Comma-separated font names", "options": [], "order": 0},
            {"label": "Number of Font Variants", "placeholder": "4",
             "field_type": "number", "is_required": True, "default_value": "2",
             "help_text": "Weight/style combinations loaded", "options": [], "order": 1},
            {"label": "Loading Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "swap",
             "help_text": "font-display value",
             "options": ["swap", "block", "fallback", "optional", "preload + self-hosted"], "order": 2},
            {"label": "Fallback Fonts", "placeholder": "system-ui, -apple-system, sans-serif",
             "field_type": "text", "is_required": False, "default_value": "system-ui, sans-serif",
             "help_text": "CSS font stack fallbacks", "options": [], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ACCESSIBILITY  (INFL-A11Y-001 … INFL-A11Y-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-A11Y-001",
        "title": "WCAG 2.2 Component Compliance Audit",
        "description": "Audit a UI component against WCAG 2.2 success criteria and generate a remediation checklist.",
        "category_slug": "accessibility",
        "template_content": (
            "Audit {{component_name}} for WCAG {{wcag_level}} compliance.\n\n"
            "Known or suspected issues:\n{{current_issues}}\n\n"
            "Generate:\n"
            "1. List of applicable WCAG 2.2 success criteria for this component\n"
            "2. Pass/Fail for each criterion with evidence\n"
            "3. Code fix for each failure\n"
            "4. axe-core rule IDs that would catch each issue\n"
            "5. Manual testing checklist (keyboard, screen reader, zoom)"
        ),
        "tags": ["accessibility", "wcag", "audit", "a11y"], "prompt_framework": "STAR",
        "subcategory": "compliance",
        "use_cases": ["a11y audit", "remediation", "compliance reporting"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Name", "placeholder": "e.g. DatePicker or ModalDialog",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Component to audit", "options": [], "order": 0},
            {"label": "WCAG Level", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "AA",
             "help_text": "Target conformance level",
             "options": ["A", "AA", "AAA"], "order": 1},
            {"label": "Known Issues", "placeholder": "No keyboard focus visible, missing aria-label on icon buttons",
             "field_type": "textarea", "is_required": False, "default_value": "",
             "help_text": "Issues already identified", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-A11Y-002",
        "title": "Keyboard Navigation Implementation",
        "description": "Implement full keyboard navigation for a complex interactive widget following WAI-ARIA patterns.",
        "category_slug": "accessibility",
        "template_content": (
            "Implement keyboard navigation for a {{component_type}} component.\n\n"
            "Required key interactions:\n{{key_interactions}}\n\n"
            "Generate:\n"
            "1. Full WAI-ARIA authoring practices keyboard interaction pattern\n"
            "2. onKeyDown handler with all required keys\n"
            "3. Roving tabindex implementation if applicable\n"
            "4. Focus trap for modal/dialog contexts\n"
            "5. useKeyboard custom hook\n"
            "6. Visual focus indicator CSS"
        ),
        "tags": ["accessibility", "keyboard", "aria", "focus"], "prompt_framework": "CO-STAR",
        "subcategory": "keyboard",
        "use_cases": ["keyboard-only users", "WCAG 2.1.1", "widget patterns"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Modal Dialog",
             "help_text": "Type of interactive widget",
             "options": ["Modal Dialog", "Dropdown Menu", "Tab Panel", "Combobox", "Date Picker", "Tree View"], "order": 0},
            {"label": "Key Interactions Required", "placeholder": "Enter: open, Escape: close, Arrow keys: navigate options",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Expected keyboard interactions", "options": [], "order": 1},
        ],
    },
    {
        "external_id": "INFL-A11Y-003",
        "title": "ARIA Roles and Properties Advisor",
        "description": "Assign correct ARIA roles, states, and properties to a custom HTML element.",
        "category_slug": "accessibility",
        "template_content": (
            "Assign correct ARIA to a custom {{html_element}} acting as {{component_role}}.\n\n"
            "Required ARIA properties:\n{{required_aria}}\n\n"
            "Dynamic state management:\n{{state_management}}\n\n"
            "Generate:\n"
            "1. Complete ARIA role + property set for the element\n"
            "2. Required owned elements (aria-owns, aria-controls)\n"
            "3. Live region setup if dynamic content\n"
            "4. React useAria or Radix UI primitive equivalent\n"
            "5. Screen reader announcement test script"
        ),
        "tags": ["accessibility", "aria", "roles", "screen-reader"], "prompt_framework": "CO-STAR",
        "subcategory": "aria",
        "use_cases": ["custom widgets", "ARIA implementation", "screen reader support"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "HTML Element", "placeholder": "e.g. div",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Base HTML element used", "options": [], "order": 0},
            {"label": "Component Role", "placeholder": "e.g. custom dropdown button",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "The semantic purpose of this element", "options": [], "order": 1},
            {"label": "Required ARIA Properties", "placeholder": "aria-expanded, aria-haspopup, aria-labelledby",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "ARIA attributes needed", "options": [], "order": 2},
            {"label": "State Management", "placeholder": "aria-expanded toggles on click; aria-selected updates on option focus",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "How ARIA states change dynamically", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-A11Y-004",
        "title": "Accessible Form Design",
        "description": "Redesign a form with proper labels, error announcements, field descriptions, and validation feedback.",
        "category_slug": "accessibility",
        "template_content": (
            "Make {{form_name}} fully accessible.\n\n"
            "Form fields: {{form_fields}}\n\n"
            "Error messaging approach: {{error_messaging_approach}}\n\n"
            "Requirements:\n"
            "- All inputs have explicit <label> or aria-labelledby\n"
            "- Error messages linked via aria-describedby\n"
            "- Required fields marked with aria-required\n"
            "- Invalid state uses aria-invalid='true'\n"
            "- Focus moves to first error on submit failure\n"
            "- Group related fields with <fieldset> + <legend>"
        ),
        "tags": ["accessibility", "forms", "aria", "validation"], "prompt_framework": "CO-STAR",
        "subcategory": "forms",
        "use_cases": ["accessible forms", "WCAG 1.3.1", "error handling"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Form Name", "placeholder": "e.g. RegistrationForm",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Form component name", "options": [], "order": 0},
            {"label": "Form Fields", "placeholder": "First name, Last name, Email, Password, Terms checkbox",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "All form fields and their types", "options": [], "order": 1},
            {"label": "Error Messaging Approach", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Inline per field",
             "help_text": "Where and how errors are shown",
             "options": ["Inline per field", "Summary at top", "Toast notification", "Aria-live region"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-A11Y-005",
        "title": "Focus Management in Single-Page Apps",
        "description": "Implement focus management for SPA route transitions, modals, and dynamic content insertions.",
        "category_slug": "accessibility",
        "template_content": (
            "Implement focus management for {{framework}} applications.\n\n"
            "Transition type: {{transition_type}}\n"
            "Focus target after transition: {{focus_target}}\n\n"
            "Generate:\n"
            "1. useFocusManagement custom hook\n"
            "2. Focus placement logic for {{transition_type}}\n"
            "3. Skip-to-content link implementation\n"
            "4. Scroll restoration strategy\n"
            "5. Screen reader announcement for page/view change"
        ),
        "tags": ["accessibility", "focus", "spa", "react"], "prompt_framework": "CO-STAR",
        "subcategory": "focus-management",
        "use_cases": ["route transitions", "modal focus trap", "dynamic content"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Framework", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "React",
             "help_text": "Frontend framework",
             "options": ["React", "Vue", "Angular", "Svelte"], "order": 0},
            {"label": "Transition Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Route Change",
             "help_text": "When focus management is needed",
             "options": ["Route Change", "Modal Open/Close", "Drawer Toggle", "Inline Expand/Collapse"], "order": 1},
            {"label": "Focus Target", "placeholder": "e.g. page h1, first form field, close button",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Element that should receive focus", "options": [], "order": 2},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # CODE REVIEW  (INFL-CR-001 … INFL-CR-010)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-CR-001",
        "title": "Pull Request Description Generator",
        "description": "Generate a comprehensive PR description with summary, test plan, screenshots placeholder, and breaking changes.",
        "category_slug": "code-review",
        "template_content": (
            "Generate a pull request description.\n\n"
            "PR Title: {{pr_title}}\n\n"
            "Summary of changes:\n{{changes_summary}}\n\n"
            "Testing done:\n{{testing_done}}\n\n"
            "Contains breaking changes: {{breaking_changes}}\n\n"
            "Generate a PR description with:\n"
            "- ## Summary (bullet list of changes)\n"
            "- ## Motivation (why these changes)\n"
            "- ## Test Plan (checklist)\n"
            "- ## Breaking Changes (if applicable)\n"
            "- ## Screenshots placeholder\n"
            "- ## Related Issues"
        ),
        "tags": ["code-review", "pr", "documentation", "github"], "prompt_framework": "CO-STAR",
        "subcategory": "pull-requests",
        "use_cases": ["PR workflow", "code review process", "documentation"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "PR Title", "placeholder": "Add user authentication with JWT",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Concise PR title", "options": [], "order": 0},
            {"label": "Changes Summary", "placeholder": "Added JWT middleware, login endpoint, refresh token rotation",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What changed and why", "options": [], "order": 1},
            {"label": "Testing Done", "placeholder": "Unit tests for JWT validation, manual login flow test",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "How you tested the changes", "options": [], "order": 2},
            {"label": "Breaking Changes", "placeholder": "",
             "field_type": "radio", "is_required": True, "default_value": "No",
             "help_text": "Does this PR contain breaking changes?",
             "options": ["Yes", "No"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-CR-002",
        "title": "Code Review Feedback Composer",
        "description": "Write professional, constructive code review feedback for a specific code snippet.",
        "category_slug": "code-review",
        "template_content": (
            "Write code review feedback.\n\n"
            "Code to review:\n{{code_snippet}}\n\n"
            "Review tone: {{review_tone}}\n"
            "Concern type: {{concern_type}}\n\n"
            "Requirements:\n"
            "- Be specific, reference line numbers\n"
            "- Explain the 'why' not just the 'what'\n"
            "- Suggest an alternative implementation\n"
            "- Use the tone: {{review_tone}}\n"
            "- End with a question to encourage dialogue"
        ),
        "tags": ["code-review", "feedback", "communication"], "prompt_framework": "CO-STAR",
        "subcategory": "review-feedback",
        "use_cases": ["code review", "mentoring", "team communication"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Code Snippet", "placeholder": "Paste the code you want to review",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Code to provide feedback on", "options": [], "order": 0},
            {"label": "Review Tone", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Constructive",
             "help_text": "Tone of the feedback",
             "options": ["Constructive", "Nitpick (non-blocking)", "Blocking", "Suggestion", "Praise"], "order": 1},
            {"label": "Concern Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Readability",
             "help_text": "Category of the concern",
             "options": ["Performance", "Security", "Readability", "Architecture", "Testing"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-CR-003",
        "title": "Security Vulnerability Assessment",
        "description": "Identify security vulnerabilities in code with OWASP classification, severity, and remediation steps.",
        "category_slug": "code-review",
        "template_content": (
            "Assess this code for security vulnerabilities.\n\n"
            "Code to assess:\n{{code_snippet}}\n\n"
            "Vulnerability type to focus on: {{vulnerability_type}}\n"
            "Severity threshold: {{severity}}\n\n"
            "Generate:\n"
            "1. List of identified vulnerabilities with OWASP category\n"
            "2. Severity rating (Critical/High/Medium/Low) per finding\n"
            "3. Proof-of-concept exploit scenario for each\n"
            "4. Remediation code for each vulnerability\n"
            "5. Security test cases to prevent regression"
        ),
        "tags": ["security", "code-review", "owasp", "vulnerabilities"], "prompt_framework": "STAR",
        "subcategory": "security",
        "use_cases": ["security review", "pen test prep", "OWASP compliance"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Code to Assess", "placeholder": "Paste the code for security review",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Code to analyze", "options": [], "order": 0},
            {"label": "Vulnerability Type to Focus On", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "All (general review)",
             "help_text": "OWASP category focus",
             "options": ["All (general review)", "XSS", "SQL Injection", "CSRF", "Auth Bypass", "Sensitive Data Exposure"], "order": 1},
            {"label": "Minimum Severity", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Medium and above",
             "help_text": "Report findings at this severity and above",
             "options": ["Critical only", "High and above", "Medium and above", "All findings"], "order": 2},

        ],
    },
    {
        "external_id": "INFL-CR-004",
        "title": "Refactoring Opportunity Identifier",
        "description": "Analyze code for refactoring opportunities and produce a prioritized refactoring plan.",
        "category_slug": "code-review",
        "template_content": (
            "Identify refactoring opportunities in this code.\n\n"
            "Code to refactor:\n{{code_snippet}}\n\n"
            "Primary refactoring goal: {{refactoring_goal}}\n\n"
            "Tasks:\n"
            "1. List all code smells with Martin Fowler catalog references\n"
            "2. Prioritize by impact vs effort matrix\n"
            "3. Show before/after for top 3 refactors\n"
            "4. Identify which refactors are safe without tests\n"
            "5. Suggest automated refactoring tools"
        ),
        "tags": ["refactoring", "code-quality", "code-review", "clean-code"], "prompt_framework": "STAR",
        "subcategory": "refactoring",
        "use_cases": ["code cleanup", "technical debt", "code quality"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Code to Refactor", "placeholder": "Paste the code to analyze",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Code for refactoring analysis", "options": [], "order": 0},
            {"label": "Primary Refactoring Goal", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Readability",
             "help_text": "Main improvement target",
             "options": ["Readability", "Performance", "Testability", "Reduce Duplication", "Simplify Logic"], "order": 1},
        ],
    },
    {
        "external_id": "INFL-CR-005",
        "title": "SOLID Principles Audit",
        "description": "Audit a class or module against SOLID principles and suggest targeted improvements.",
        "category_slug": "code-review",
        "template_content": (
            "Audit {{class_or_module}} against SOLID principles.\n\n"
            "Code:\n{{code_snippet}}\n\n"
            "Principles to check: {{principles_to_check}}\n\n"
            "For each SOLID principle:\n"
            "1. Pass/Fail assessment\n"
            "2. Evidence from the code\n"
            "3. Concrete refactoring suggestion\n"
            "4. Refactored code snippet\n"
            "5. Unit test that validates the improvement"
        ),
        "tags": ["solid", "oop", "code-review", "architecture"], "prompt_framework": "STAR",
        "subcategory": "architecture",
        "use_cases": ["OOP review", "design principles", "architecture audit"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Class or Module Name", "placeholder": "e.g. UserService",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Name of the class/module to audit", "options": [], "order": 0},
            {"label": "Code Snippet", "placeholder": "Paste the class or module code",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Full source to audit", "options": [], "order": 1},
            {"label": "Principles to Check", "placeholder": "SRP, OCP (leave blank for all)",
             "field_type": "text", "is_required": False, "default_value": "All (S O L I D)",
             "help_text": "Which SOLID principles to focus on", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-CR-006",
        "title": "Tech Debt Documentation Generator",
        "description": "Document a tech debt item with context, impact, remediation plan, and effort estimate.",
        "category_slug": "code-review",
        "template_content": (
            "Document tech debt in the area: {{tech_debt_area}}.\n\n"
            "Current implementation:\n{{current_implementation}}\n\n"
            "Desired state:\n{{desired_state}}\n\n"
            "Effort estimate: {{effort_estimate}}\n\n"
            "Generate a tech debt ticket with:\n"
            "- Problem statement and root cause\n"
            "- Business impact (velocity, risk, reliability)\n"
            "- Step-by-step remediation plan\n"
            "- Definition of Done\n"
            "- Links to relevant files/PRs\n"
            "- Risk of NOT addressing this debt"
        ),
        "tags": ["tech-debt", "documentation", "engineering"], "prompt_framework": "CO-STAR",
        "subcategory": "tech-debt",
        "use_cases": ["tech debt tracking", "sprint planning", "backlog grooming"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Tech Debt Area", "placeholder": "e.g. Authentication module",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Module or area affected", "options": [], "order": 0},
            {"label": "Current Implementation", "placeholder": "Describe the current state and what is wrong",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What exists now", "options": [], "order": 1},
            {"label": "Desired State", "placeholder": "What the ideal implementation looks like",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Target architecture", "options": [], "order": 2},
            {"label": "Effort Estimate", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Days",
             "help_text": "Rough effort to remediate",
             "options": ["Hours", "Days", "Weeks", "Months"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-CR-007",
        "title": "Dependency Audit & Update Strategy",
        "description": "Audit npm dependencies for vulnerabilities, outdated packages, and generate a safe update strategy.",
        "category_slug": "code-review",
        "template_content": (
            "Audit npm dependencies.\n\n"
            "Package.json dependencies:\n{{package_json_excerpt}}\n\n"
            "Known security vulnerabilities:\n{{security_vulnerabilities}}\n\n"
            "Update strategy: {{update_strategy}}\n\n"
            "Generate:\n"
            "1. Packages to update immediately (CVE severity >= High)\n"
            "2. Major version bumps requiring migration guides\n"
            "3. Safe patch/minor updates to batch\n"
            "4. Deprecated packages to replace\n"
            "5. npm audit fix --force vs manual update guidance\n"
            "6. Testing strategy for dependency updates"
        ),
        "tags": ["dependencies", "security", "npm", "audit"], "prompt_framework": "STAR",
        "subcategory": "dependencies",
        "use_cases": ["security patching", "dependency management", "supply chain security"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Package.json Dependencies", "placeholder": "Paste your dependencies and devDependencies",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Current package.json dependency section", "options": [], "order": 0},
            {"label": "Known Vulnerabilities", "placeholder": "Paste npm audit output or CVE IDs",
             "field_type": "textarea", "is_required": False, "default_value": "",
             "help_text": "Output from npm audit", "options": [], "order": 1},
            {"label": "Update Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Conservative (patch only)",
             "help_text": "How aggressive to be with updates",
             "options": ["Conservative (patch only)", "Moderate (patch + minor)", "Aggressive (all including major)"], "order": 2},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # API DESIGN  (INFL-API-001 … INFL-API-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-API-001",
        "title": "REST API Endpoint Design",
        "description": "Design a production-ready REST API endpoint with request/response schemas, status codes, and error handling.",
        "category_slug": "api-design",
        "template_content": (
            "Design a REST API endpoint for {{resource_name}}.\n\n"
            "HTTP method: {{http_method}}\n\n"
            "Request schema:\n{{request_schema}}\n\n"
            "Success response schema:\n{{response_schema}}\n\n"
            "Generate:\n"
            "1. Full endpoint specification (URL, method, headers)\n"
            "2. Request validation rules\n"
            "3. HTTP status codes for all scenarios (2xx, 4xx, 5xx)\n"
            "4. Error response format following RFC 7807\n"
            "5. Rate limiting headers\n"
            "6. cURL example request"
        ),
        "tags": ["api", "rest", "design", "http"], "prompt_framework": "CO-STAR",
        "subcategory": "rest",
        "use_cases": ["API design", "endpoint specification", "API documentation"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Resource Name", "placeholder": "e.g. User or Project",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "The resource this endpoint manages", "options": [], "order": 0},
            {"label": "HTTP Method", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "POST",
             "help_text": "HTTP verb",
             "options": ["GET", "POST", "PUT", "PATCH", "DELETE"], "order": 1},
            {"label": "Request Schema", "placeholder": "{ name: string, email: string, role: string }",
             "field_type": "textarea", "is_required": False, "default_value": "",
             "help_text": "JSON request body schema", "options": [], "order": 2},
            {"label": "Response Schema", "placeholder": "{ id: uuid, name: string, createdAt: datetime }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "JSON success response schema", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-API-002",
        "title": "OpenAPI / Swagger Spec Generator",
        "description": "Generate an OpenAPI 3.1 specification for an API endpoint with all required fields.",
        "category_slug": "api-design",
        "template_content": (
            "Generate an OpenAPI 3.1 spec for API: {{api_title}} v{{version}}.\n\n"
            "Endpoint descriptions:\n{{endpoint_summary}}\n\n"
            "Auth type: {{auth_type}}\n\n"
            "Generate:\n"
            "1. Complete openapi.yaml with info, servers, paths\n"
            "2. SecuritySchemes for {{auth_type}}\n"
            "3. Reusable components/schemas for request/response bodies\n"
            "4. Proper HTTP status code responses per endpoint\n"
            "5. examples for each schema"
        ),
        "tags": ["openapi", "swagger", "api", "specification"], "prompt_framework": "CO-STAR",
        "subcategory": "specification",
        "use_cases": ["API docs", "SDK generation", "contract testing"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "API Title", "placeholder": "e.g. MyApp REST API",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "API name for the spec", "options": [], "order": 0},
            {"label": "Version", "placeholder": "1.0.0",
             "field_type": "text", "is_required": True, "default_value": "1.0.0",
             "help_text": "SemVer version", "options": [], "order": 1},
            {"label": "Endpoint Summary", "placeholder": "POST /users - create user\nGET /users/{id} - get user by id",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Brief description of each endpoint", "options": [], "order": 2},
            {"label": "Auth Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Bearer JWT",
             "help_text": "Security scheme",
             "options": ["Bearer JWT", "API Key Header", "OAuth2 PKCE", "Basic Auth", "None"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-API-003",
        "title": "API Pagination Strategy Designer",
        "description": "Choose and implement the right pagination strategy (offset, cursor, keyset) for a given dataset.",
        "category_slug": "api-design",
        "template_content": (
            "Design pagination for the {{resource_name}} API endpoint.\n\n"
            "Dataset size: {{dataset_size}}\n"
            "Pagination type: {{pagination_type}}\n\n"
            "Generate:\n"
            "1. Query parameter spec for {{pagination_type}} pagination\n"
            "2. Response envelope with pagination metadata\n"
            "3. Database query implementation (SQL or ORM)\n"
            "4. Link header (RFC 5988) or next/prev cursor tokens\n"
            "5. Performance considerations and index requirements\n"
            "6. Client-side consumption example"
        ),
        "tags": ["api", "pagination", "database", "performance"], "prompt_framework": "CO-STAR",
        "subcategory": "pagination",
        "use_cases": ["list endpoints", "infinite scroll API", "feed API"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Resource Name", "placeholder": "e.g. Posts",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Resource being paginated", "options": [], "order": 0},
            {"label": "Dataset Size", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Medium (1k–100k rows)",
             "help_text": "Expected table size",
             "options": ["Small (<1k rows)", "Medium (1k–100k rows)", "Large (>100k rows)"], "order": 1},
            {"label": "Pagination Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Cursor-based",
             "help_text": "Pagination strategy",
             "options": ["Offset / Limit", "Cursor-based", "Keyset (seek method)", "Page-based"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-API-004",
        "title": "API Error Response Standardizer",
        "description": "Standardize API error responses following RFC 7807 Problem Details with machine-readable error codes.",
        "category_slug": "api-design",
        "template_content": (
            "Standardize error responses for the API.\n\n"
            "Error scenario: {{error_scenario}}\n"
            "HTTP status code: {{http_status_code}}\n"
            "Internal error code: {{error_code}}\n"
            "Response format: {{response_format}}\n\n"
            "Generate:\n"
            "1. Error response JSON for this scenario\n"
            "2. Error enum/const for all application errors\n"
            "3. Middleware/decorator to format all errors consistently\n"
            "4. Client-side error type guard in TypeScript\n"
            "5. Documentation for error code registry"
        ),
        "tags": ["api", "errors", "rfc-7807", "standardization"], "prompt_framework": "CO-STAR",
        "subcategory": "error-handling",
        "use_cases": ["error standardization", "API design", "client error handling"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Error Scenario", "placeholder": "e.g. User not found",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Human description of the error", "options": [], "order": 0},
            {"label": "HTTP Status Code", "placeholder": "404",
             "field_type": "number", "is_required": True, "default_value": "400",
             "help_text": "HTTP status code to return", "options": [], "order": 1},
            {"label": "Internal Error Code", "placeholder": "USER_NOT_FOUND",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Machine-readable error code", "options": [], "order": 2},
            {"label": "Response Format", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "RFC 7807 Problem Details",
             "help_text": "Error response schema standard",
             "options": ["RFC 7807 Problem Details", "Custom JSON", "JSend", "JSON:API Errors"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-API-005",
        "title": "Webhook Design & Security",
        "description": "Design a secure webhook system with HMAC signature verification, retry strategy, and idempotency.",
        "category_slug": "api-design",
        "template_content": (
            "Design a webhook system for event: {{event_type}}.\n\n"
            "Payload schema:\n{{payload_schema}}\n\n"
            "Security mechanism: {{security_mechanism}}\n"
            "Retry strategy: {{retry_strategy}}\n\n"
            "Generate:\n"
            "1. Webhook payload JSON schema\n"
            "2. {{security_mechanism}} verification code (sender and receiver)\n"
            "3. Idempotency key strategy\n"
            "4. Retry logic with {{retry_strategy}}\n"
            "5. Dead-letter queue for failed deliveries\n"
            "6. Consumer implementation example"
        ),
        "tags": ["api", "webhook", "security", "hmac"], "prompt_framework": "CO-STAR",
        "subcategory": "webhooks",
        "use_cases": ["event-driven architecture", "third-party integrations", "Stripe-style webhooks"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Event Type", "placeholder": "e.g. payment.succeeded",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Dot-notation event name", "options": [], "order": 0},
            {"label": "Payload Schema", "placeholder": "{ id: uuid, event: string, data: { amount: number } }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "JSON payload structure", "options": [], "order": 1},
            {"label": "Security Mechanism", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "HMAC-SHA256 Signature",
             "help_text": "How to verify webhook authenticity",
             "options": ["HMAC-SHA256 Signature", "Bearer Token Header", "IP Whitelist", "mTLS"], "order": 2},
            {"label": "Retry Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Exponential Backoff",
             "help_text": "Failed delivery retry approach",
             "options": ["Exponential Backoff", "Fixed Interval (1h)", "Immediate + 3 retries", "None"], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # TESTING & QA  (INFL-TEST-001 … INFL-TEST-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-TEST-001",
        "title": "Unit Test Suite Generator (Vitest / Jest)",
        "description": "Generate a comprehensive unit test suite for a function with happy path, edge cases, and mocking.",
        "category_slug": "testing-qa",
        "template_content": (
            "Generate a unit test suite for {{function_name}}.\n\n"
            "Function code:\n{{function_code}}\n\n"
            "Edge cases to cover:\n{{edge_cases}}\n\n"
            "Test framework: {{test_framework}}\n\n"
            "Requirements:\n"
            "- describe/it blocks with descriptive names\n"
            "- AAA pattern (Arrange, Act, Assert)\n"
            "- Mock all external dependencies\n"
            "- Test all edge cases listed above\n"
            "- Aim for 100% branch coverage\n"
            "- Include error cases"
        ),
        "tags": ["testing", "unit-test", "vitest", "jest", "tdd"], "prompt_framework": "CO-STAR",
        "subcategory": "unit-testing",
        "use_cases": ["unit tests", "TDD", "regression prevention"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Function Name", "placeholder": "e.g. calculateDiscount",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Name of the function to test", "options": [], "order": 0},
            {"label": "Function Code", "placeholder": "Paste the function implementation",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Source code to test", "options": [], "order": 1},
            {"label": "Edge Cases to Cover", "placeholder": "empty input, null values, boundary values, network errors",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Specific cases to test", "options": [], "order": 2},
            {"label": "Test Framework", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Vitest",
             "help_text": "Testing framework",
             "options": ["Vitest", "Jest", "Mocha + Chai", "Node test runner"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-TEST-002",
        "title": "React Testing Library Component Tests",
        "description": "Write RTL tests for a React component focusing on user behavior, accessibility queries, and async interactions.",
        "category_slug": "testing-qa",
        "template_content": (
            "Write React Testing Library tests for {{component_name}}.\n\n"
            "Component code:\n{{component_code}}\n\n"
            "User interactions to test:\n{{user_interactions}}\n\n"
            "Key assertions:\n{{assertions}}\n\n"
            "Requirements:\n"
            "- Query by role/label (no data-testid unless necessary)\n"
            "- userEvent over fireEvent\n"
            "- Test async operations with waitFor\n"
            "- Mock fetch/API calls with MSW\n"
            "- Test error states and loading states"
        ),
        "tags": ["testing", "rtl", "react", "component-testing"], "prompt_framework": "CO-STAR",
        "subcategory": "component-testing",
        "use_cases": ["component tests", "user interaction tests", "accessibility testing"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Name", "placeholder": "e.g. LoginForm",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Component to test", "options": [], "order": 0},
            {"label": "Component Code", "placeholder": "Paste the component source",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Component implementation", "options": [], "order": 1},
            {"label": "User Interactions to Test", "placeholder": "Click submit, type in fields, select dropdown",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "User actions to simulate", "options": [], "order": 2},
            {"label": "Key Assertions", "placeholder": "Error shown on invalid email, redirect on success",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What to assert after interactions", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-TEST-003",
        "title": "E2E Test Scenario (Playwright)",
        "description": "Write a Playwright E2E test for a complete user journey with selectors, assertions, and CI config.",
        "category_slug": "testing-qa",
        "template_content": (
            "Write a Playwright E2E test for {{feature_name}}.\n\n"
            "User journey:\n{{user_journey}}\n\n"
            "Test environment: {{test_environment}}\n"
            "Browser target: {{browser_target}}\n\n"
            "Requirements:\n"
            "- Page Object Model (POM) structure\n"
            "- Semantic locators (getByRole, getByLabel)\n"
            "- Network request interception for API calls\n"
            "- Screenshot on failure\n"
            "- Parallel execution config\n"
            "- playwright.config.ts setup"
        ),
        "tags": ["testing", "playwright", "e2e", "automation"], "prompt_framework": "CO-STAR",
        "subcategory": "e2e-testing",
        "use_cases": ["E2E automation", "smoke tests", "regression suite"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Feature Name", "placeholder": "e.g. User Checkout Flow",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Feature being tested", "options": [], "order": 0},
            {"label": "User Journey", "placeholder": "1. Navigate to /products\n2. Add item to cart\n3. Checkout\n4. Payment\n5. Confirm order",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Step-by-step user flow", "options": [], "order": 1},
            {"label": "Test Environment", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Staging",
             "help_text": "Target environment for tests",
             "options": ["Local", "Staging", "Production (read-only)"], "order": 2},
            {"label": "Browser Target", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Chromium only",
             "help_text": "Playwright browser(s) to use",
             "options": ["Chromium only", "Firefox only", "WebKit only", "All browsers"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-TEST-004",
        "title": "Test Data Factory Builder",
        "description": "Create a test data factory with sensible defaults, type safety, and partial override support.",
        "category_slug": "testing-qa",
        "template_content": (
            "Create a test data factory for {{model_name}}.\n\n"
            "Model fields:\n{{model_fields}}\n\n"
            "Factory library: {{factory_library}}\n\n"
            "Override strategy:\n{{override_strategy}}\n\n"
            "Requirements:\n"
            "- Default values for all required fields\n"
            "- Partial override with TypeScript Partial<T>\n"
            "- Sequence-based unique fields (id, email)\n"
            "- Related model factories\n"
            "- buildList(n) helper function"
        ),
        "tags": ["testing", "factories", "test-data", "typescript"], "prompt_framework": "CO-STAR",
        "subcategory": "test-data",
        "use_cases": ["test fixtures", "seed data", "unit test setup"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Model Name", "placeholder": "e.g. User",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "The model to build a factory for", "options": [], "order": 0},
            {"label": "Model Fields", "placeholder": "id: uuid, name: string, email: string, role: admin|user, createdAt: Date",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "All fields with their types", "options": [], "order": 1},
            {"label": "Factory Library", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "fishery (TypeScript)",
             "help_text": "Factory library to use",
             "options": ["fishery (TypeScript)", "@faker-js/faker", "factory-boy (Python)", "Custom builder"], "order": 2},
            {"label": "Override Strategy", "placeholder": "Allow partial overrides for each test case",
             "field_type": "textarea", "is_required": False, "default_value": "Partial field overrides via spread",
             "help_text": "How consumers customize factory output", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-TEST-005",
        "title": "TDD Red-Green-Refactor Cycle",
        "description": "Guide a full TDD cycle for a feature: failing test → minimal implementation → refactor.",
        "category_slug": "testing-qa",
        "template_content": (
            "Guide a TDD cycle for feature: {{feature_name}}.\n\n"
            "Acceptance criteria:\n{{acceptance_criteria}}\n\n"
            "Test framework: {{test_framework}}\n\n"
            "Generate in order:\n"
            "1. RED: Write failing tests for each criterion\n"
            "2. GREEN: Write minimal implementation to pass all tests\n"
            "3. REFACTOR: Improve implementation without changing tests\n"
            "4. Coverage report checklist\n"
            "5. Commit message for each phase"
        ),
        "tags": ["tdd", "testing", "red-green-refactor", "bdd"], "prompt_framework": "CO-STAR",
        "subcategory": "tdd",
        "use_cases": ["TDD practice", "feature development", "test-first development"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Feature Name", "placeholder": "e.g. User password reset",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Feature to develop with TDD", "options": [], "order": 0},
            {"label": "Acceptance Criteria", "placeholder": "1. User receives reset email\n2. Token expires in 1 hour\n3. Old password rejected after reset",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Each criterion becomes a test", "options": [], "order": 1},
            {"label": "Test Framework", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Vitest",
             "help_text": "Testing framework",
             "options": ["Vitest", "Jest", "PyTest", "RSpec", "Go testing"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-TEST-006",
        "title": "API Contract Testing with MSW",
        "description": "Set up Mock Service Worker (MSW) handlers for API contract testing in unit and E2E tests.",
        "category_slug": "testing-qa",
        "template_content": (
            "Set up MSW contract tests for endpoint {{endpoint}}.\n\n"
            "Request schema:\n{{request_schema}}\n\n"
            "Response schema:\n{{response_schema}}\n\n"
            "Error cases to mock:\n{{error_cases}}\n\n"
            "Generate:\n"
            "1. MSW handler for happy path\n"
            "2. MSW handlers for each error case\n"
            "3. server.ts setup for Node.js (Vitest/Jest)\n"
            "4. browser.ts setup for browser tests\n"
            "5. Contract validation against OpenAPI schema\n"
            "6. Test examples using each handler"
        ),
        "tags": ["testing", "msw", "api", "mocking", "contract"], "prompt_framework": "CO-STAR",
        "subcategory": "api-testing",
        "use_cases": ["API mocking", "contract testing", "offline testing"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Endpoint", "placeholder": "POST /api/auth/login",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "API endpoint to mock", "options": [], "order": 0},
            {"label": "Request Schema", "placeholder": "{ email: string, password: string }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Expected request body", "options": [], "order": 1},
            {"label": "Success Response Schema", "placeholder": "{ token: string, user: { id: string, email: string } }",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "200 response body", "options": [], "order": 2},
            {"label": "Error Cases", "placeholder": "401 invalid credentials, 429 rate limited, 503 service unavailable",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Error scenarios to mock", "options": [], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # DEVOPS & CI/CD  (INFL-DEVOPS-001 … INFL-DEVOPS-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-DEVOPS-001",
        "title": "GitHub Actions CI Workflow Generator",
        "description": "Generate a complete GitHub Actions CI workflow with test, lint, build, and optional deploy jobs.",
        "category_slug": "devops-cicd",
        "template_content": (
            "Generate a GitHub Actions workflow named {{workflow_name}}.\n\n"
            "Trigger events: {{trigger_events}}\n\n"
            "Jobs to include:\n{{jobs_description}}\n\n"
            "Deployment environment: {{environment}}\n\n"
            "Generate:\n"
            "1. .github/workflows/{{workflow_name}}.yml\n"
            "2. Job dependency chain (needs:)\n"
            "3. Caching for node_modules and build artifacts\n"
            "4. Matrix strategy for Node.js versions if applicable\n"
            "5. Environment protection rules\n"
            "6. Status badge markdown"
        ),
        "tags": ["ci-cd", "github-actions", "devops", "automation"], "prompt_framework": "CO-STAR",
        "subcategory": "ci-cd",
        "use_cases": ["CI pipeline", "automated testing", "deployment automation"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Workflow Name", "placeholder": "e.g. ci",
             "field_type": "text", "is_required": True, "default_value": "ci",
             "help_text": "Filename-safe workflow name", "options": [], "order": 0},
            {"label": "Trigger Events", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "push + pull_request",
             "help_text": "When this workflow runs",
             "options": ["push + pull_request", "pull_request only", "push to main only", "schedule + manual"], "order": 1},
            {"label": "Jobs to Include", "placeholder": "lint, test, build, deploy to Heroku",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "List of CI jobs", "options": [], "order": 2},
            {"label": "Deployment Environment", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "staging",
             "help_text": "Target environment for deploy job",
             "options": ["none (CI only)", "staging", "production", "both (staging + production)"], "order": 3},
        ],
    },
    {
        "external_id": "INFL-DEVOPS-002",
        "title": "Docker Multi-Stage Build",
        "description": "Create an optimized Docker multi-stage build for a production application with minimal final image.",
        "category_slug": "devops-cicd",
        "template_content": (
            "Create a Docker multi-stage Dockerfile for a {{app_type}} app named {{app_name}}.\n\n"
            "Exposed port: {{exposed_port}}\n"
            "Base image: {{base_image}}\n\n"
            "Generate:\n"
            "1. Multi-stage Dockerfile (deps → builder → runner)\n"
            "2. .dockerignore file\n"
            "3. Docker Compose for local development\n"
            "4. Health check configuration\n"
            "5. Non-root user setup\n"
            "6. Build command and run command"
        ),
        "tags": ["docker", "devops", "containers", "ci-cd"], "prompt_framework": "CO-STAR",
        "subcategory": "containers",
        "use_cases": ["containerization", "production deploy", "CI builds"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "App Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Node.js",
             "help_text": "Application runtime",
             "options": ["Node.js", "Python", "Go", "Java", "Rust"], "order": 0},
            {"label": "App Name", "placeholder": "e.g. my-api",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Docker image name", "options": [], "order": 1},
            {"label": "Exposed Port", "placeholder": "8000",
             "field_type": "number", "is_required": True, "default_value": "3000",
             "help_text": "Container port to expose", "options": [], "order": 2},
            {"label": "Base Image", "placeholder": "node:20-alpine",
             "field_type": "text", "is_required": False, "default_value": "node:20-alpine",
             "help_text": "Docker base image", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-DEVOPS-003",
        "title": "Heroku Release Phase & Deployment Runbook",
        "description": "Write a Heroku Procfile release phase script and full deployment runbook for zero-downtime deploys.",
        "category_slug": "devops-cicd",
        "template_content": (
            "Write a Heroku deployment runbook for {{app_name}}.\n\n"
            "Release phase tasks:\n{{release_tasks}}\n\n"
            "Rollback plan:\n{{rollback_plan}}\n\n"
            "Generate:\n"
            "1. Procfile with web and release entries\n"
            "2. release.sh script for {{release_tasks}}\n"
            "3. Pre-deploy checklist\n"
            "4. Step-by-step deployment procedure\n"
            "5. Monitoring checks after deploy\n"
            "6. Rollback procedure: {{rollback_plan}}\n"
            "7. Heroku CLI commands for each step"
        ),
        "tags": ["heroku", "devops", "deployment", "runbook"], "prompt_framework": "CO-STAR",
        "subcategory": "deployment",
        "use_cases": ["Heroku deployment", "release automation", "zero-downtime deploy"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "App Name", "placeholder": "e.g. my-production-app",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Heroku app name", "options": [], "order": 0},
            {"label": "Release Phase Tasks", "placeholder": "Run DB migrations, seed lookup tables, clear cache",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Tasks to run before new dynos start", "options": [], "order": 1},
            {"label": "Rollback Plan", "placeholder": "heroku rollback if migration fails, feature flag disable",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "How to recover from a bad deploy", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-DEVOPS-004",
        "title": "Environment Variable Management Plan",
        "description": "Design a secure environment variable strategy across local, staging, and production environments.",
        "category_slug": "devops-cicd",
        "template_content": (
            "Design an environment variable strategy for {{app_name}}.\n\n"
            "Variables to manage:\n{{env_vars_list}}\n\n"
            "Secrets manager: {{secrets_manager}}\n\n"
            "Generate:\n"
            "1. Categorize vars: public, private, secrets\n"
            "2. .env.example with all keys (no real values)\n"
            "3. Validation schema using Zod or envalid\n"
            "4. {{secrets_manager}} setup instructions\n"
            "5. CI/CD secrets injection pattern\n"
            "6. Secret rotation procedure"
        ),
        "tags": ["devops", "environment-variables", "secrets", "security"], "prompt_framework": "CO-STAR",
        "subcategory": "configuration",
        "use_cases": ["secret management", "12-factor app", "security"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "App Name", "placeholder": "e.g. my-saas-app",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Application name", "options": [], "order": 0},
            {"label": "Environment Variables List", "placeholder": "DATABASE_URL, SECRET_KEY, STRIPE_KEY, REDIS_URL",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "All env vars (names only)", "options": [], "order": 1},
            {"label": "Secrets Manager", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Heroku Config Vars",
             "help_text": "Where secrets are stored",
             "options": ["Heroku Config Vars", "AWS Secrets Manager", "GitHub Secrets + Actions", "Doppler", ".env files only"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-DEVOPS-005",
        "title": "Database Migration Safety Checklist",
        "description": "Generate a pre/post migration safety checklist for zero-downtime database schema changes.",
        "category_slug": "devops-cicd",
        "template_content": (
            "Create a migration safety plan for a {{migration_type}} on table {{table_name}}.\n\n"
            "Estimated row count: {{estimated_rows}}\n\n"
            "Rollback script:\n{{rollback_script}}\n\n"
            "Generate:\n"
            "1. Pre-migration checklist (backup, locks, traffic)\n"
            "2. Migration script with safety annotations\n"
            "3. Estimated migration duration and lock time\n"
            "4. Zero-downtime pattern (expand-contract if needed)\n"
            "5. Post-migration validation queries\n"
            "6. Rollback procedure using: {{rollback_script}}\n"
            "7. Django/Alembic specific commands"
        ),
        "tags": ["database", "migration", "devops", "zero-downtime"], "prompt_framework": "STAR",
        "subcategory": "database",
        "use_cases": ["schema migrations", "zero-downtime DB changes", "production safety"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Migration Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Add Column",
             "help_text": "Type of schema change",
             "options": ["Add Column", "Drop Column", "Add Index", "Rename Column", "Data Backfill", "Schema Change"], "order": 0},
            {"label": "Table Name", "placeholder": "e.g. users",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Database table being modified", "options": [], "order": 1},
            {"label": "Estimated Row Count", "placeholder": "500000",
             "field_type": "number", "is_required": True, "default_value": "10000",
             "help_text": "Approximate number of rows in table", "options": [], "order": 2},
            {"label": "Rollback Script", "placeholder": "ALTER TABLE users DROP COLUMN new_field;",
             "field_type": "textarea", "is_required": False, "default_value": "",
             "help_text": "SQL to undo this migration", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-DEVOPS-006",
        "title": "Sentry Error Monitoring Setup",
        "description": "Integrate Sentry for error tracking, performance monitoring, and release tracking in a web application.",
        "category_slug": "devops-cicd",
        "template_content": (
            "Set up Sentry monitoring for {{project_name}} ({{framework}}).\n\n"
            "Performance tracing enabled: {{performance_tracing}}\n\n"
            "Generate:\n"
            "1. Sentry SDK initialization with DSN environment variable\n"
            "2. Source maps upload in CI/CD\n"
            "3. Release tracking with git SHA\n"
            "4. Custom error boundary with Sentry.ErrorBoundary\n"
            "5. User context attachment (user.id, user.email)\n"
            "6. Custom tags and breadcrumbs for {{project_name}}\n"
            "7. Alert rules for new issues and regressions"
        ),
        "tags": ["monitoring", "sentry", "devops", "error-tracking"], "prompt_framework": "CO-STAR",
        "subcategory": "monitoring",
        "use_cases": ["error monitoring", "production observability", "performance tracing"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Project Name", "placeholder": "e.g. my-production-app",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Sentry project name", "options": [], "order": 0},
            {"label": "Framework", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Next.js",
             "help_text": "Application framework",
             "options": ["Next.js", "React SPA", "Django", "FastAPI", "Express.js"], "order": 1},
            {"label": "Performance Tracing", "placeholder": "",
             "field_type": "radio", "is_required": True, "default_value": "Yes",
             "help_text": "Enable Sentry performance monitoring?",
             "options": ["Yes", "No"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-DEVOPS-007",
        "title": "Lighthouse CI Integration",
        "description": "Set up Lighthouse CI to enforce performance, accessibility, and SEO score thresholds in CI pipelines.",
        "category_slug": "devops-cicd",
        "template_content": (
            "Set up Lighthouse CI for {{project_name}}.\n\n"
            "Categories to measure: {{lighthouse_categories}}\n"
            "Score thresholds:\n{{score_thresholds}}\n\n"
            "CI provider: {{ci_provider}}\n\n"
            "Generate:\n"
            "1. lighthouserc.json configuration\n"
            "2. {{ci_provider}} job definition\n"
            "3. LHCI server setup or Temporary Public Storage config\n"
            "4. PR comment integration showing score diffs\n"
            "5. Budget assertions for bundle size and CWV\n"
            "6. Local audit script: npm run lhci"
        ),
        "tags": ["lighthouse", "performance", "ci-cd", "quality-gates"], "prompt_framework": "CO-STAR",
        "subcategory": "quality-gates",
        "use_cases": ["performance budgets", "accessibility CI", "quality gates"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Project Name", "placeholder": "e.g. my-marketing-site",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Project name for LHCI", "options": [], "order": 0},
            {"label": "Categories to Measure", "placeholder": "performance, accessibility, seo, best-practices",
             "field_type": "text", "is_required": True, "default_value": "performance, accessibility, seo",
             "help_text": "Lighthouse audit categories", "options": [], "order": 1},
            {"label": "Score Thresholds", "placeholder": "performance >= 80, accessibility >= 95, seo >= 90",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Minimum passing scores", "options": [], "order": 2},
            {"label": "CI Provider", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "GitHub Actions",
             "help_text": "Where LHCI runs",
             "options": ["GitHub Actions", "CircleCI", "GitLab CI", "Jenkins"], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL: FRONTEND  (INFL-FE-010)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-FE-010",
        "title": "React State Machine with useReducer",
        "description": "Model complex component state as a finite state machine using useReducer and discriminated actions.",
        "category_slug": "frontend-dev",
        "template_content": (
            "Model {{state_machine_name}} as a finite state machine.\n\n"
            "Possible states:\n{{states}}\n\n"
            "Actions / transitions:\n{{actions}}\n\n"
            "Initial state:\n{{initial_state}}\n\n"
            "Generate:\n"
            "1. State and Action TypeScript discriminated unions\n"
            "2. reducer function with exhaustive switch\n"
            "3. useStateMachine custom hook wrapping useReducer\n"
            "4. State guard functions (isLoading, isError, etc.)\n"
            "5. Usage example in a component"
        ),
        "tags": ["react", "state-machine", "use-reducer", "typescript"], "prompt_framework": "CO-STAR",
        "subcategory": "state-management",
        "use_cases": ["async state", "wizard steps", "complex UI state"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "State Machine Name", "placeholder": "e.g. UploadStateMachine",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Descriptive name for the machine", "options": [], "order": 0},
            {"label": "Possible States", "placeholder": "idle, uploading, success, error",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Comma-separated state names", "options": [], "order": 1},
            {"label": "Actions", "placeholder": "START_UPLOAD, UPLOAD_SUCCESS, UPLOAD_ERROR, RESET",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Events that trigger transitions", "options": [], "order": 2},
            {"label": "Initial State", "placeholder": "idle",
             "field_type": "text", "is_required": True, "default_value": "idle",
             "help_text": "Starting state name", "options": [], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL: NEXT.JS  (INFL-NX-010)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-NX-010",
        "title": "Next.js Parallel Routes & Intercepting Routes",
        "description": "Implement Next.js parallel routes for modal patterns and intercepting routes for contextual UI.",
        "category_slug": "nextjs-react",
        "template_content": (
            "Implement a Next.js parallel + intercepting route pattern for {{feature_name}}.\n\n"
            "Slot layout: {{slot_layout}}\n"
            "Modal route path: {{modal_route}}\n\n"
            "Generate:\n"
            "1. layout.tsx with @modal parallel slot\n"
            "2. (..)route/page.tsx as intercepting route\n"
            "3. Actual page.tsx for direct URL access\n"
            "4. Modal wrapper component with close button\n"
            "5. Navigation link that triggers interception\n"
            "6. Explanation of when interception fires vs falls through"
        ),
        "tags": ["nextjs", "parallel-routes", "intercepting-routes", "modal"], "prompt_framework": "CO-STAR",
        "subcategory": "routing",
        "use_cases": ["modal patterns", "photo gallery", "contextual overlays"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Feature Name", "placeholder": "e.g. Photo Viewer",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "The feature using this pattern", "options": [], "order": 0},
            {"label": "Slot Layout", "placeholder": "Feed page with @modal slot beside main content",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Describe the parallel slot arrangement", "options": [], "order": 1},
            {"label": "Modal Route Path", "placeholder": "/photos/[id]",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Route that opens as modal when intercepted", "options": [], "order": 2},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL: CSS  (INFL-CSS-006 … INFL-CSS-008)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-CSS-006",
        "title": "CSS Container Query Pattern",
        "description": "Replace media queries with CSS container queries for truly component-level responsive design.",
        "category_slug": "css-styling",
        "template_content": (
            "Implement CSS container queries for {{component_name}}.\n\n"
            "Container name: {{container_name}}\n"
            "Layout changes at different container sizes:\n{{layout_changes}}\n"
            "Minimum inline size breakpoint: {{min_inline_size}}\n\n"
            "Generate:\n"
            "1. container-type and container-name declaration\n"
            "2. @container query rules for each breakpoint\n"
            "3. Tailwind @container plugin config (if using Tailwind)\n"
            "4. Fallback media query for unsupported browsers\n"
            "5. JavaScript feature detection snippet"
        ),
        "tags": ["css", "container-queries", "responsive", "modern-css"], "prompt_framework": "CO-STAR",
        "subcategory": "responsive-design",
        "use_cases": ["component responsiveness", "design system", "card layouts"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Name", "placeholder": "e.g. ProductCard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Component to make container-responsive", "options": [], "order": 0},
            {"label": "Container Name", "placeholder": "e.g. card-container",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "CSS container name identifier", "options": [], "order": 1},
            {"label": "Layout Changes", "placeholder": "< 300px: stacked; 300-500px: side-by-side; > 500px: full card with image",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What changes at each container size", "options": [], "order": 2},
            {"label": "Minimum Inline Size", "placeholder": "300px",
             "field_type": "text", "is_required": False, "default_value": "300px",
             "help_text": "Smallest container width breakpoint", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-CSS-007",
        "title": "Tailwind CSS Plugin Generator",
        "description": "Create a custom Tailwind CSS plugin that adds new utilities, components, or base styles.",
        "category_slug": "css-styling",
        "template_content": (
            "Create a Tailwind CSS plugin named {{plugin_name}}.\n\n"
            "Utilities to add:\n{{utilities_to_add}}\n\n"
            "Theme extension:\n{{plugin_theme_extension}}\n\n"
            "Generate:\n"
            "1. plugin() definition with addUtilities, addComponents, addBase\n"
            "2. Theme values accessible via theme() function\n"
            "3. Responsive and state variants (hover, focus)\n"
            "4. tailwind.config.ts integration\n"
            "5. TypeScript intellisense types for custom classes"
        ),
        "tags": ["tailwind", "plugin", "css", "design-system"], "prompt_framework": "APE",
        "subcategory": "design-system",
        "use_cases": ["custom utilities", "brand-specific styles", "component primitives"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Plugin Name", "placeholder": "e.g. tailwind-plugin-brand",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Plugin identifier name", "options": [], "order": 0},
            {"label": "Utilities to Add", "placeholder": ".text-gradient, .glass-morphism, .animate-shimmer",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Custom CSS classes to generate", "options": [], "order": 1},
            {"label": "Theme Extension", "placeholder": "brandColors, gradients, animations",
             "field_type": "textarea", "is_required": False, "default_value": "",
             "help_text": "Theme tokens to extend", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-CSS-008",
        "title": "CSS Architecture Pattern (BEM / ITCSS)",
        "description": "Design a scalable CSS architecture using BEM naming or ITCSS layering for large projects.",
        "category_slug": "css-styling",
        "template_content": (
            "Design a CSS architecture for {{project_name}}.\n\n"
            "Architecture approach: {{architecture_approach}}\n"
            "Number of components: {{component_count}}\n"
            "Team size: {{team_size}}\n\n"
            "Generate:\n"
            "1. Folder structure with naming conventions\n"
            "2. Layer/namespace definitions\n"
            "3. BEM naming examples for 3 components\n"
            "4. Import order (globals → utilities → components)\n"
            "5. ESLint/Stylelint rules to enforce the architecture\n"
            "6. Migration guide from current flat CSS"
        ),
        "tags": ["css", "architecture", "bem", "itcss", "scalability"], "prompt_framework": "CO-STAR",
        "subcategory": "architecture",
        "use_cases": ["large codebase CSS", "team CSS standards", "refactoring CSS"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Project Name", "placeholder": "e.g. enterprise-dashboard",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Project name", "options": [], "order": 0},
            {"label": "Architecture Approach", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "ITCSS + BEM",
             "help_text": "CSS methodology",
             "options": ["BEM only", "ITCSS + BEM", "SMACSS", "Atomic CSS + Tailwind"], "order": 1},
            {"label": "Approximate Component Count", "placeholder": "50",
             "field_type": "number", "is_required": False, "default_value": "20",
             "help_text": "Number of UI components", "options": [], "order": 2},
            {"label": "Team Size", "placeholder": "5",
             "field_type": "number", "is_required": False, "default_value": "3",
             "help_text": "Number of engineers working on CSS", "options": [], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL: PERFORMANCE  (INFL-PERF-007, INFL-PERF-008)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-PERF-007",
        "title": "Critical CSS Extraction Strategy",
        "description": "Extract and inline above-the-fold critical CSS to eliminate render-blocking stylesheets.",
        "category_slug": "web-performance",
        "template_content": (
            "Extract critical CSS for the above-the-fold content.\n\n"
            "Above-the-fold content:\n{{above_fold_content}}\n\n"
            "Total stylesheet size: {{stylesheet_size}}\n"
            "Render-blocking resources:\n{{render_blocking_resources}}\n\n"
            "Generate:\n"
            "1. Critical CSS extraction approach (Critters, critical, or manual)\n"
            "2. Inline <style> block for critical CSS\n"
            "3. Non-critical CSS async loading pattern\n"
            "4. Next.js / Vite plugin config for automation\n"
            "5. Before/after render timeline comparison"
        ),
        "tags": ["performance", "critical-css", "render-blocking", "fcp"], "prompt_framework": "STAR",
        "subcategory": "critical-path",
        "use_cases": ["FCP optimization", "render-blocking elimination", "LCP improvement"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Above-Fold Content", "placeholder": "Hero section: navbar, headline, CTA button, hero image",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Elements visible without scrolling", "options": [], "order": 0},
            {"label": "Total Stylesheet Size", "placeholder": "e.g. 280KB",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Combined CSS size", "options": [], "order": 1},
            {"label": "Render-Blocking Resources", "placeholder": "3 CSS files, 2 Google Fonts links",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Blocking resources identified in DevTools", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-PERF-008",
        "title": "Image Optimization Checklist Generator",
        "description": "Generate a complete image optimization checklist and implementation plan for a web project.",
        "category_slug": "web-performance",
        "template_content": (
            "Generate an image optimization plan for {{image_context}}.\n\n"
            "Current image format: {{current_format}}\n"
            "Lazy loading implemented: {{lazy_loading}}\n"
            "CDN in use: {{cdn_used}}\n\n"
            "Generate:\n"
            "1. Format migration plan (WebP/AVIF with fallback)\n"
            "2. Responsive srcset and sizes attributes\n"
            "3. Lazy loading implementation\n"
            "4. CDN configuration for image transforms\n"
            "5. CLS prevention (explicit width/height or aspect-ratio)\n"
            "6. Compression settings and quality recommendations"
        ),
        "tags": ["performance", "images", "webp", "avif", "lazy-loading"], "prompt_framework": "CO-STAR",
        "subcategory": "images",
        "use_cases": ["image performance", "LCP optimization", "CLS reduction"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Image Context", "placeholder": "E-commerce product listing page",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Where images are used", "options": [], "order": 0},
            {"label": "Current Format", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "JPEG",
             "help_text": "Existing image format",
             "options": ["JPEG", "PNG", "WebP", "AVIF", "SVG", "Mixed"], "order": 1},
            {"label": "Lazy Loading Implemented", "placeholder": "",
             "field_type": "radio", "is_required": True, "default_value": "No",
             "help_text": "Is lazy loading already set up?",
             "options": ["Yes", "No"], "order": 2},
            {"label": "CDN in Use", "placeholder": "Cloudflare / Cloudinary / none",
             "field_type": "text", "is_required": False, "default_value": "none",
             "help_text": "Image CDN or delivery service", "options": [], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL: ACCESSIBILITY  (INFL-A11Y-006 … INFL-A11Y-008)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-A11Y-006",
        "title": "Color Contrast & Color Blindness Reviewer",
        "description": "Audit color combinations for WCAG contrast ratios and color-blindness safe usage.",
        "category_slug": "accessibility",
        "template_content": (
            "Audit color usage for {{component_context}}.\n\n"
            "Text color (hex): {{text_color}}\n"
            "Background color (hex): {{background_color}}\n"
            "Text size category: {{text_size}}\n\n"
            "Generate:\n"
            "1. Contrast ratio calculation and WCAG grade (A/AA/AAA)\n"
            "2. Suggested replacement colors if failing\n"
            "3. Color-blindness simulation notes (deuteranopia, protanopia)\n"
            "4. CSS custom property update recommendations\n"
            "5. Automated contrast check with postcss-colorblind or Storybook a11y addon"
        ),
        "tags": ["accessibility", "color", "contrast", "wcag", "color-blindness"], "prompt_framework": "STAR",
        "subcategory": "color",
        "use_cases": ["color audit", "WCAG 1.4.3", "inclusive design"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Text Color (hex)", "placeholder": "#6B7280",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Foreground color hex value", "options": [], "order": 0},
            {"label": "Background Color (hex)", "placeholder": "#FFFFFF",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Background color hex value", "options": [], "order": 1},
            {"label": "Text Size Category", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Normal text (<18pt)",
             "help_text": "WCAG text size classification",
             "options": ["Normal text (<18pt)", "Large text (>=18pt or 14pt bold)", "UI Component / Graphic"], "order": 2},
            {"label": "Component Context", "placeholder": "e.g. form placeholder text",
             "field_type": "text", "is_required": False, "default_value": "",
             "help_text": "Where this color combination is used", "options": [], "order": 3},
        ],
    },
    {
        "external_id": "INFL-A11Y-007",
        "title": "Screen Reader Live Region Announcer",
        "description": "Implement ARIA live regions for dynamic content announcements in React applications.",
        "category_slug": "accessibility",
        "template_content": (
            "Implement screen reader announcements for {{dynamic_event}}.\n\n"
            "Announcement type: {{announcement_type}}\n"
            "Live region content: {{live_region_content}}\n\n"
            "Generate:\n"
            "1. VisuallyHidden announcement component\n"
            "2. aria-live='{{announcement_type}}' region placement\n"
            "3. useAnnounce custom hook\n"
            "4. Timing strategy (avoid announcement on mount)\n"
            "5. Test with VoiceOver / NVDA script"
        ),
        "tags": ["accessibility", "aria-live", "screen-reader", "announcements"], "prompt_framework": "CO-STAR",
        "subcategory": "aria",
        "use_cases": ["dynamic content", "status messages", "form feedback"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Dynamic Event", "placeholder": "File upload completion, form submission error",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What triggers the announcement", "options": [], "order": 0},
            {"label": "Announcement Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "polite",
             "help_text": "aria-live value",
             "options": ["polite", "assertive", "off (manual trigger)"], "order": 1},
            {"label": "Live Region Content", "placeholder": "Upload complete: report.pdf (2.3MB)",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Example message to announce", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-A11Y-008",
        "title": "Skip Navigation & Landmark Regions",
        "description": "Implement skip-to-content links and ARIA landmark regions for efficient keyboard and AT navigation.",
        "category_slug": "accessibility",
        "template_content": (
            "Implement skip navigation and landmarks for: {{page_layout}}.\n\n"
            "Skip link targets:\n{{skip_link_targets}}\n\n"
            "Landmark structure: {{landmark_structure}}\n\n"
            "Generate:\n"
            "1. Visually-hidden skip link that shows on focus\n"
            "2. CSS for focus-visible skip link\n"
            "3. HTML landmark structure (header, nav, main, aside, footer)\n"
            "4. aria-label for multiple nav landmarks\n"
            "5. React component: SkipNavigation\n"
            "6. Screen reader navigation test script"
        ),
        "tags": ["accessibility", "skip-nav", "landmarks", "keyboard"], "prompt_framework": "CO-STAR",
        "subcategory": "navigation",
        "use_cases": ["WCAG 2.4.1", "keyboard navigation", "AT navigation"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Page Layout Description", "placeholder": "Dashboard with top nav, left sidebar, main content, footer",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Describe the page regions", "options": [], "order": 0},
            {"label": "Skip Link Targets", "placeholder": "#main-content, #navigation, #search",
             "field_type": "textarea", "is_required": True, "default_value": "#main-content",
             "help_text": "IDs of areas users can skip to", "options": [], "order": 1},
            {"label": "Landmark Structure", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Standard (header/main/footer)",
             "help_text": "Page complexity",
             "options": ["Simple (header/main/footer)", "Standard (header/main/footer)", "Complex (multiple nav + aside)", "SPA (dynamic regions)"], "order": 2},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL: CODE REVIEW  (INFL-CR-008 … INFL-CR-010)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-CR-008",
        "title": "React Anti-Pattern Detector",
        "description": "Detect and fix common React anti-patterns: prop drilling, side effects in render, stale closures.",
        "category_slug": "code-review",
        "template_content": (
            "Detect React anti-patterns in the following component.\n\n"
            "Component code:\n{{component_code}}\n\n"
            "Category to focus on: {{anti_pattern_category}}\n\n"
            "Generate:\n"
            "1. List of identified anti-patterns with React docs reference\n"
            "2. Explanation of why each is harmful\n"
            "3. Refactored code fixing each anti-pattern\n"
            "4. ESLint rules that would have caught these (eslint-plugin-react-hooks)\n"
            "5. Test to verify the fix works correctly"
        ),
        "tags": ["react", "anti-patterns", "code-review", "best-practices"], "prompt_framework": "STAR",
        "subcategory": "react",
        "use_cases": ["code review", "React best practices", "bug prevention"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Code", "placeholder": "Paste the React component to review",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Component source to analyze", "options": [], "order": 0},
            {"label": "Anti-Pattern Category", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "All (general review)",
             "help_text": "Category to focus on",
             "options": ["All (general review)", "State Management", "Side Effects / useEffect", "Performance / Re-renders", "Prop Drilling", "Key Prop Usage"], "order": 1},
        ],
    },
    {
        "external_id": "INFL-CR-009",
        "title": "Dead Code & Complexity Analyzer",
        "description": "Identify dead code, unused exports, and high cyclomatic complexity in a module.",
        "category_slug": "code-review",
        "template_content": (
            "Analyze {{module_path}} for dead code and complexity.\n\n"
            "Module code:\n{{code_snippet}}\n\n"
            "Cyclomatic complexity threshold: {{complexity_threshold}}\n\n"
            "Generate:\n"
            "1. List unused variables, functions, and exports\n"
            "2. Cyclomatic complexity score per function\n"
            "3. Functions exceeding threshold: refactoring suggestions\n"
            "4. ESLint / ts-prune / knip configuration to automate detection\n"
            "5. Prioritized removal/simplification plan"
        ),
        "tags": ["code-review", "dead-code", "complexity", "refactoring"], "prompt_framework": "STAR",
        "subcategory": "code-quality",
        "use_cases": ["codebase cleanup", "complexity reduction", "bundle size reduction"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Module Path", "placeholder": "src/utils/helpers.ts",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Relative path to the module", "options": [], "order": 0},
            {"label": "Module Code", "placeholder": "Paste the module source",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "Source to analyze", "options": [], "order": 1},
            {"label": "Complexity Threshold", "placeholder": "10",
             "field_type": "number", "is_required": False, "default_value": "10",
             "help_text": "Max cyclomatic complexity before flagging", "options": [], "order": 2},
        ],
    },
    {
        "external_id": "INFL-CR-010",
        "title": "API Rate Limiting & Throttling Design",
        "description": "Design a rate limiting strategy for an API endpoint with quota tiers, headers, and backpressure handling.",
        "category_slug": "api-design",
        "template_content": (
            "Design rate limiting for API endpoint: {{api_endpoint}}.\n\n"
            "Expected RPS: {{expected_rps}}\n"
            "Client type: {{client_type}}\n"
            "Action when limit exceeded: {{throttle_action}}\n\n"
            "Generate:\n"
            "1. Rate limit tiers (free, pro, enterprise)\n"
            "2. Token bucket or sliding window algorithm choice with justification\n"
            "3. Response headers: X-RateLimit-Limit, Remaining, Reset\n"
            "4. 429 response body with Retry-After header\n"
            "5. Redis implementation for distributed rate limiting\n"
            "6. Django REST Framework throttle class config"
        ),
        "tags": ["api", "rate-limiting", "throttling", "performance"], "prompt_framework": "CO-STAR",
        "subcategory": "rate-limiting",
        "use_cases": ["API protection", "abuse prevention", "quota management"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "API Endpoint", "placeholder": "POST /api/ai/generate",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Endpoint to apply rate limiting to", "options": [], "order": 0},
            {"label": "Expected RPS", "placeholder": "100",
             "field_type": "number", "is_required": True, "default_value": "10",
             "help_text": "Expected requests per second at peak", "options": [], "order": 1},
            {"label": "Client Type", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Authenticated User",
             "help_text": "Who is being rate-limited",
             "options": ["Authenticated User", "Anonymous / IP-based", "API Key", "Service Account"], "order": 2},
            {"label": "Action When Limit Exceeded", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Return 429 with Retry-After",
             "help_text": "What happens when quota is hit",
             "options": ["Return 429 with Retry-After", "Queue request", "Degrade gracefully", "Block for 24h"], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL: TESTING  (INFL-TEST-007 … INFL-TEST-008)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-TEST-007",
        "title": "Accessibility Test Automation (axe-core)",
        "description": "Set up automated accessibility testing with axe-core in Vitest, Jest, and Playwright.",
        "category_slug": "testing-qa",
        "template_content": (
            "Set up accessibility test automation for {{component_name}}.\n\n"
            "Test tool: {{test_tool}}\n"
            "WCAG level: {{wcag_level}}\n\n"
            "Generate:\n"
            "1. axe-core / jest-axe configuration\n"
            "2. Accessibility test for {{component_name}}\n"
            "3. Custom rule configuration for project-specific rules\n"
            "4. CI integration to fail on new violations\n"
            "5. Baseline snapshot to track regressions\n"
            "6. Report generation for audit trail"
        ),
        "tags": ["accessibility", "testing", "axe-core", "automation", "a11y"], "prompt_framework": "CO-STAR",
        "subcategory": "accessibility-testing",
        "use_cases": ["a11y CI gate", "automated audits", "WCAG compliance"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Component Name", "placeholder": "e.g. NavigationMenu",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Component to test", "options": [], "order": 0},
            {"label": "Test Tool", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "jest-axe",
             "help_text": "Accessibility testing library",
             "options": ["jest-axe", "Playwright + axe-core", "cypress-axe", "Vitest + axe-core"], "order": 1},
            {"label": "WCAG Level", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "AA",
             "help_text": "WCAG conformance level to test against",
             "options": ["A", "AA", "AAA"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-TEST-008",
        "title": "Visual Regression Testing Setup",
        "description": "Configure visual regression testing with screenshot comparisons and CI gating.",
        "category_slug": "testing-qa",
        "template_content": (
            "Set up visual regression testing for {{project_name}}.\n\n"
            "VRT tool: {{vrt_tool}}\n"
            "Baseline branch: {{baseline_branch}}\n"
            "Acceptable diff threshold: {{threshold_percentage}}%\n\n"
            "Generate:\n"
            "1. VRT tool configuration file\n"
            "2. CI job definition for screenshot capture and comparison\n"
            "3. Storybook integration (if applicable)\n"
            "4. PR comment with diff report\n"
            "5. Baseline update workflow\n"
            "6. Per-component test examples"
        ),
        "tags": ["testing", "visual-regression", "screenshots", "ci-cd"], "prompt_framework": "CO-STAR",
        "subcategory": "visual-testing",
        "use_cases": ["UI regression prevention", "design system testing", "cross-browser visual"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Project Name", "placeholder": "e.g. design-system",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Project to set up VRT for", "options": [], "order": 0},
            {"label": "VRT Tool", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Playwright Screenshots",
             "help_text": "Visual regression testing tool",
             "options": ["Playwright Screenshots", "Chromatic + Storybook", "Percy", "BackstopJS"], "order": 1},
            {"label": "Baseline Branch", "placeholder": "main",
             "field_type": "text", "is_required": True, "default_value": "main",
             "help_text": "Branch with approved baseline screenshots", "options": [], "order": 2},
            {"label": "Diff Threshold (%)", "placeholder": "0.1",
             "field_type": "number", "is_required": False, "default_value": "0",
             "help_text": "Max pixel diff % before failing", "options": [], "order": 3},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL: DEVOPS  (INFL-DEVOPS-008 … INFL-DEVOPS-009)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "external_id": "INFL-DEVOPS-008",
        "title": "Blue-Green Deployment Strategy",
        "description": "Design a blue-green deployment strategy for zero-downtime releases with traffic switching and rollback.",
        "category_slug": "devops-cicd",
        "template_content": (
            "Design a blue-green deployment strategy for {{application_name}}.\n\n"
            "Infrastructure: {{infrastructure}}\n"
            "Database migration strategy: {{database_migration_strategy}}\n\n"
            "Generate:\n"
            "1. Blue-green environment setup and naming\n"
            "2. Traffic switching mechanism\n"
            "3. Health check gates before traffic switch\n"
            "4. Database migration approach: {{database_migration_strategy}}\n"
            "5. Rollback trigger conditions and procedure\n"
            "6. Smoke test suite to run against green before switch"
        ),
        "tags": ["devops", "blue-green", "deployment", "zero-downtime"], "prompt_framework": "CO-STAR",
        "subcategory": "deployment",
        "use_cases": ["zero-downtime deploys", "rollback strategy", "production safety"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "Application Name", "placeholder": "e.g. my-api",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Application being deployed", "options": [], "order": 0},
            {"label": "Infrastructure", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Heroku",
             "help_text": "Hosting platform",
             "options": ["Heroku", "AWS ECS", "GCP Cloud Run", "Kubernetes", "Vercel / Netlify"], "order": 1},
            {"label": "Database Migration Strategy", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "Backward Compatible (default)",
             "help_text": "How DB changes are handled",
             "options": ["Backward Compatible (default)", "Dual Write", "Expand-Contract pattern", "Separate migration PR"], "order": 2},
        ],
    },
    {
        "external_id": "INFL-DEVOPS-009",
        "title": "API Versioning Strategy",
        "description": "Design a sustainable API versioning strategy with deprecation policy and client migration guide.",
        "category_slug": "api-design",
        "template_content": (
            "Design an API versioning strategy for {{api_name}}.\n\n"
            "Current version: {{current_version}}\n\n"
            "Breaking change introduced:\n{{breaking_change_description}}\n\n"
            "Versioning approach: {{versioning_approach}}\n\n"
            "Generate:\n"
            "1. Version identifier format (v1, 2024-01-01, etc.)\n"
            "2. Implementation of {{versioning_approach}}\n"
            "3. Deprecation header (Sunset, Deprecation)\n"
            "4. Side-by-side version coexistence period\n"
            "5. Client migration guide\n"
            "6. Django REST Framework or FastAPI versioning config"
        ),
        "tags": ["api", "versioning", "backward-compatibility", "rest"], "prompt_framework": "CO-STAR",
        "subcategory": "versioning",
        "use_cases": ["breaking changes", "API lifecycle", "client compatibility"],
        "is_premium_required": False, "required_subscription": "free",
        "token_cost": 0, "copy_limit_per_day": None,
        "fields": [
            {"label": "API Name", "placeholder": "e.g. MyApp REST API",
             "field_type": "text", "is_required": True, "default_value": "",
             "help_text": "Name of the API", "options": [], "order": 0},
            {"label": "Current Version", "placeholder": "v1",
             "field_type": "text", "is_required": True, "default_value": "v1",
             "help_text": "Current API version", "options": [], "order": 1},
            {"label": "Breaking Change Description", "placeholder": "Renamed 'user_id' to 'id' in all responses",
             "field_type": "textarea", "is_required": True, "default_value": "",
             "help_text": "What changed that breaks existing clients", "options": [], "order": 2},
            {"label": "Versioning Approach", "placeholder": "",
             "field_type": "dropdown", "is_required": True, "default_value": "URL Path (/v2/)",
             "help_text": "How to communicate version to API",
             "options": ["URL Path (/v2/)", "Accept Header", "Query Parameter (?version=2)", "Date-based (2025-01-01)"], "order": 3},
        ],
    },
]


# ── COMMAND ───────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = (
        "Inflate the database with professional developer-focused prompt templates "
        "(idempotent — safe to re-run)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Preview what would be created without writing to the DB.",
        )
        parser.add_argument(
            "--rollback", action="store_true",
            help="Delete all templates whose external_id starts with INFL-.",
        )
        parser.add_argument(
            "--category", type=str, default=None,
            help="Only process templates for this category slug.",
        )
        parser.add_argument(
            "--batch-size", type=int, default=10,
            help="Process templates in batches of this size (default: 10).",
        )
        parser.add_argument(
            "--verbose", action="store_true",
            help="Print detailed progress per template.",
        )

    # ── main entry ────────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        rollback = options["rollback"]
        category_filter = options.get("category")
        batch_size = max(1, options.get("batch_size", 10))
        verbose = options.get("verbose", False) or options.get("verbosity", 1) >= 2

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "[DRY RUN] No changes will be written to the database."
            ))

        if rollback:
            self._rollback(dry_run=dry_run, verbose=verbose)
            return

        category_map = self._seed_categories(dry_run=dry_run, verbose=verbose)
        seed_user = self._get_seed_user()

        dataset = TEMPLATES_DATASET
        if category_filter:
            dataset = [t for t in dataset if t["category_slug"] == category_filter]
            if not dataset:
                raise CommandError(
                    f"No templates found for category slug: '{category_filter}'\n"
                    f"Available: {sorted({t['category_slug'] for t in TEMPLATES_DATASET})}"
                )

        created = skipped = errors = 0

        for i in range(0, len(dataset), batch_size):
            batch = dataset[i : i + batch_size]
            for record in batch:
                result = self._create_template(
                    record=record,
                    category_map=category_map,
                    seed_user=seed_user,
                    dry_run=dry_run,
                    verbose=verbose,
                )
                if result == "created":
                    created += 1
                elif result == "skipped":
                    skipped += 1
                else:
                    errors += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nInflation complete — "
            f"Created: {created} | Skipped (already exist): {skipped} | Errors: {errors}"
        ))

    # ── helpers ───────────────────────────────────────────────────────────────

    def _seed_categories(self, dry_run: bool, verbose: bool) -> dict:
        """Get-or-create all categories and return a slug → instance map."""
        category_map: dict = {}

        for cat_data in CATEGORIES_DATASET:
            slug = cat_data["slug"]
            if dry_run:
                category_map[slug] = None
                if verbose:
                    self.stdout.write(f"  [DRY] Category: {cat_data['name']}")
                continue

            cat, created = TemplateCategory.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "icon": cat_data.get("icon", ""),
                    "color": cat_data.get("color", "#6366F1"),
                    "order": cat_data.get("order", 0),
                    "is_active": True,
                },
            )
            category_map[slug] = cat
            if verbose and created:
                self.stdout.write(f"  + Category: {cat.name}")

        return category_map

    def _get_seed_user(self):
        """Return a superuser or create a dedicated seed user."""
        user = User.objects.filter(is_superuser=True).order_by("date_joined").first()
        if not user:
            user, _ = User.objects.get_or_create(
                username="inflate_seed",
                defaults={
                    "email": "inflate@seed.internal",
                    "is_staff": False,
                    "is_active": True,
                },
            )
        return user

    def _create_template(
        self,
        record: dict,
        category_map: dict,
        seed_user,
        dry_run: bool,
        verbose: bool,
    ) -> str:
        ext_id = record["external_id"]
        title = record["title"]

        if Template.objects.filter(external_id=ext_id).exists():
            if verbose:
                self.stdout.write(f"  ~ Skip (exists): [{ext_id}] {title}")
            return "skipped"

        if dry_run:
            self.stdout.write(f"  [DRY] Would create: [{ext_id}] {title}")
            return "created"

        category = category_map.get(record["category_slug"])
        if category is None:
            self.stderr.write(self.style.ERROR(
                f"  ! Category not found: '{record['category_slug']}' — skipping [{ext_id}]"
            ))
            return "error"

        try:
            with transaction.atomic():
                # 1. bulk-create PromptField objects
                fields_data = record.get("fields", [])
                pf_objects = [
                    PromptField(
                        label=fd["label"],
                        placeholder=fd.get("placeholder", ""),
                        field_type=fd.get("field_type", "text"),
                        is_required=fd.get("is_required", False),
                        default_value=fd.get("default_value", ""),
                        help_text=fd.get("help_text", ""),
                        options=fd.get("options", []),
                        order=fd.get("order", 0),
                    )
                    for fd in fields_data
                ]
                created_fields = PromptField.objects.bulk_create(pf_objects)

                # 2. create Template
                template = Template.objects.create(
                    title=title,
                    description=record.get("description", ""),
                    category=category,
                    template_content=record["template_content"],
                    author=seed_user,
                    version="1.0.0",
                    tags=record.get("tags", []),
                    is_public=True,
                    is_featured=False,
                    is_active=True,
                    external_id=ext_id,
                    prompt_framework=record.get("prompt_framework", ""),
                    subcategory=record.get("subcategory", ""),
                    use_cases=record.get("use_cases", []),
                    is_premium_required=record.get("is_premium_required", False),
                    required_subscription=record.get("required_subscription", "free"),
                    token_cost=record.get("token_cost", 0),
                    copy_limit_per_day=record.get("copy_limit_per_day"),
                )

                # 3. link via TemplateField through model
                for order_idx, pf in enumerate(created_fields):
                    TemplateField.objects.create(
                        template=template,
                        field=pf,
                        order=order_idx,
                    )

            if verbose:
                self.stdout.write(self.style.SUCCESS(
                    f"  + Created: [{ext_id}] {title} ({len(created_fields)} fields)"
                ))
            return "created"

        except Exception as exc:
            self.stderr.write(self.style.ERROR(
                f"  ! Error [{ext_id}] {title}: {exc}"
            ))
            return "error"

    def _rollback(self, dry_run: bool, verbose: bool):
        """Remove all templates seeded by this command (external_id starts with INFL-)."""
        qs = Template.objects.filter(external_id__startswith="INFL-")
        count = qs.count()

        if count == 0:
            self.stdout.write("No INFL-* templates found — nothing to roll back.")
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"[DRY] Would delete {count} INFL-* template(s)."
            ))
            return

        if verbose:
            for t in qs:
                self.stdout.write(f"  - Deleting: [{t.external_id}] {t.title}")

        deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Rollback complete — deleted {deleted} template(s)."
        ))
