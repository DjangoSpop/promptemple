"""
inflate_pro_prompts
===================
Seeds the database with 60 curated, professional plain-text prompts across
10 high-monetisation categories. Designed for the Discover page.

Idempotent: uses get_or_create on (title, category) so running it multiple
times never creates duplicates.

Usage:
    python manage.py inflate_pro_prompts
    python manage.py inflate_pro_prompts --dry-run
    python manage.py inflate_pro_prompts --clear
    python manage.py inflate_pro_prompts --category "Software Engineering"
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()

# ---------------------------------------------------------------------------
# Prompt library
# ---------------------------------------------------------------------------
# Each entry:  (title, description, content, tags, usage_count_seed)
# category key maps to the CATEGORIES dict below.

CATEGORIES = {
    "Business Writing": {"icon": "briefcase", "color": "#3B82F6", "order": 1},
    "Marketing & Copywriting": {"icon": "megaphone", "color": "#8B5CF6", "order": 2},
    "Sales & Growth": {"icon": "trending-up", "color": "#10B981", "order": 3},
    "Software Engineering": {"icon": "code", "color": "#F59E0B", "order": 4},
    "Data & Analytics": {"icon": "bar-chart", "color": "#EF4444", "order": 5},
    "Productivity & Operations": {"icon": "zap", "color": "#06B6D4", "order": 6},
    "Content Creation": {"icon": "pen-tool", "color": "#EC4899", "order": 7},
    "Legal & Compliance": {"icon": "shield", "color": "#6B7280", "order": 8},
    "HR & Recruiting": {"icon": "users", "color": "#F97316", "order": 9},
    "Customer Success": {"icon": "heart", "color": "#14B8A6", "order": 10},
}

PRO_PROMPTS = {
    # ── Business Writing ────────────────────────────────────────────────────
    "Business Writing": [
        (
            "Executive Summary Writer",
            "Generate a crisp, boardroom-ready executive summary from any document or set of bullet points.",
            """You are a senior management consultant. Write an executive summary based on the information provided below.

Requirements:
- Start with a one-sentence conclusion (the 'so-what')
- 3–5 bullet points covering context, key findings, and recommendations
- End with a clear call to action
- Tone: authoritative, concise, no jargon
- Maximum 250 words

Information to summarise:
[PASTE YOUR CONTENT HERE]""",
            ["executive", "summary", "business", "strategy", "leadership"],
            412,
        ),
        (
            "Business Proposal Generator",
            "Draft a compelling business proposal that wins clients and secures deals.",
            """You are a proposal writer with 15 years of enterprise sales experience.
Write a professional business proposal with these sections:
1. Executive Overview (2 sentences)
2. Problem Statement – articulate the client's pain clearly
3. Proposed Solution – what you will deliver and why it's unique
4. Scope of Work – concrete deliverables and timeline
5. Pricing & ROI – frame cost as investment
6. Why Us – 3 differentiators
7. Next Steps – specific call to action

Context:
- Client: [CLIENT NAME & INDUSTRY]
- Their main challenge: [CHALLENGE]
- Our offering: [PRODUCT / SERVICE]
- Budget range: [BUDGET]""",
            ["proposal", "business development", "sales", "B2B", "enterprise"],
            388,
        ),
        (
            "Stakeholder Update Email",
            "Write a clear, concise project status email that keeps stakeholders aligned without meeting fatigue.",
            """Write a professional stakeholder update email for a project.

Format:
- Subject line: compelling, informative
- Opening: 1-sentence status pulse (on track / at risk / blocked)
- Accomplishments this period: 3 bullets
- Upcoming milestones: 2–3 bullets with owners and dates
- Risks & blockers: flag only what needs attention
- Ask: one specific action item from the reader (if any)
- Sign-off: warm but professional

Project details:
- Project name: [NAME]
- Period covered: [DATES]
- Key updates: [YOUR NOTES]
- Any risks: [RISKS]""",
            ["email", "stakeholder", "project management", "communication"],
            295,
        ),
        (
            "Board Presentation Outline",
            "Structure a board deck that answers the questions every board member is actually thinking.",
            """You are a CFO preparing a board presentation. Create a slide-by-slide outline that covers:

Slide 1 – Company pulse: one headline metric and trend
Slide 2 – Key achievements vs. last board meeting commitments
Slide 3 – Financial performance: revenue, gross margin, burn (actuals vs. plan)
Slide 4 – Top 3 strategic priorities for next quarter with owners
Slide 5 – Key risks and mitigation strategies (max 3)
Slide 6 – Resource needs or decisions required from the board
Slide 7 – Appendix: supporting data

For each slide include: speaker notes (2–3 sentences), the single key message, and one data point that supports it.

Company context:
- Stage: [STAGE]
- Industry: [INDUSTRY]
- Period: [QUARTER / YEAR]
- Top priority: [PRIORITY]""",
            ["board", "investors", "presentation", "strategy", "fundraising"],
            271,
        ),
        (
            "Performance Review Writer",
            "Write balanced, evidence-based performance reviews that motivate employees and satisfy HR.",
            """Write a professional performance review for an employee.

Structure:
1. Overall performance summary (2–3 sentences, balanced)
2. Top 3 strengths with specific examples
3. 2–3 development areas with constructive, forward-looking language
4. Goal achievement – assess each goal provided
5. Goals for next period – SMART, tied to team objectives
6. Overall rating justification

Employee context:
- Role: [ROLE]
- Review period: [PERIOD]
- Key goals this period: [GOALS]
- Achievements to highlight: [ACHIEVEMENTS]
- Areas for improvement: [AREAS]
- Desired overall rating: [RATING e.g. Exceeds / Meets / Below Expectations]""",
            ["HR", "performance review", "management", "employee", "feedback"],
            234,
        ),
        (
            "Meeting Agenda Creator",
            "Design a tight, purpose-driven meeting agenda that respects everyone's time.",
            """Create a professional meeting agenda that ensures the meeting achieves its objective.

For each agenda item include:
- Time allocation (in minutes)
- Owner
- Desired outcome (decision / information / discussion)
- Pre-read or preparation needed

Meeting details:
- Purpose: [WHY IS THIS MEETING HAPPENING?]
- Duration: [TOTAL MINUTES]
- Attendees & roles: [LIST]
- Items to cover: [YOUR BULLET POINTS]
- Decisions needed: [ANY DECISIONS]

End with a 'parking lot' section for topics that emerge but are out of scope.""",
            ["meeting", "agenda", "productivity", "facilitation", "operations"],
            198,
        ),
    ],

    # ── Marketing & Copywriting ─────────────────────────────────────────────
    "Marketing & Copywriting": [
        (
            "AIDA Sales Copy Framework",
            "Write high-converting sales copy using the proven Attention-Interest-Desire-Action structure.",
            """You are a world-class direct response copywriter. Write sales copy using the AIDA framework.

ATTENTION – Open with a bold hook that stops the scroll. Use a surprising stat, provocative question, or vivid pain point.

INTEREST – Explain the problem in detail. Make the reader feel understood. Use 'you' language.

DESIRE – Present the solution. Focus on transformation and outcomes, not features. Use social proof (stats, testimonials).

ACTION – Clear, urgent CTA. Remove friction. Handle the final objection.

Product/Service details:
- Name: [PRODUCT]
- Target customer: [PERSONA]
- Core benefit: [MAIN BENEFIT]
- Price point: [PRICE]
- Key proof point: [SOCIAL PROOF OR STAT]
- CTA destination: [URL / ACTION]""",
            ["copywriting", "AIDA", "sales", "conversion", "direct response"],
            521,
        ),
        (
            "Email Subject Line Generator",
            "Generate 10 high-open-rate subject lines for any email campaign using proven psychological triggers.",
            """You are an email marketing specialist with a track record of 40%+ open rates.

Generate 10 subject lines for the email described below. For each subject line:
- Apply a different psychological trigger: curiosity, urgency, social proof, personalisation, fear of missing out, benefit-led, question, number, controversy, or surprise
- Keep it under 50 characters where possible
- Write a 1-sentence explanation of why it will work

Email context:
- Campaign type: [NEWSLETTER / PROMO / ONBOARDING / RE-ENGAGEMENT]
- Audience: [SEGMENT]
- Main message: [WHAT THE EMAIL IS ABOUT]
- Desired action: [WHAT YOU WANT THEM TO DO]
- Brand voice: [FORMAL / CASUAL / PLAYFUL]""",
            ["email marketing", "subject line", "open rate", "copywriting", "campaign"],
            487,
        ),
        (
            "Landing Page Hero Copy",
            "Write the above-the-fold copy (headline, subheadline, CTA) that captures attention and drives sign-ups.",
            """Write the hero section copy for a landing page. This is the most important section — it must answer three questions in 5 seconds: What is it? Who is it for? What do I get?

Deliver:
1. Headline (max 8 words) – bold transformation or outcome
2. Subheadline (1–2 sentences) – expand on who it's for and the key benefit
3. 3 benefit bullets (verb-led, specific, outcome-focused)
4. Primary CTA button text (3–5 words, action verb)
5. Below-button trust line (e.g. "Join 12,000+ marketers" or "No credit card required")
6. One alternative headline to A/B test

Product details:
- Product: [NAME]
- ICP: [IDEAL CUSTOMER PROFILE]
- Core value proposition: [VALUE PROP]
- Key differentiator: [WHAT MAKES IT DIFFERENT]""",
            ["landing page", "conversion", "copywriting", "CRO", "SaaS"],
            463,
        ),
        (
            "Brand Positioning Statement",
            "Craft a crisp brand positioning statement that differentiates you in a crowded market.",
            """You are a brand strategist. Write a brand positioning statement and the supporting messaging architecture.

1. One-line positioning statement using the format:
   "For [target customer] who [need/pain], [brand] is the [category] that [benefit] because [reason to believe]."

2. Brand promise (1 sentence employees can remember and deliver on)

3. Three brand pillars (values that everything you say and do must reflect)

4. Messaging for each audience segment:
   - Customers: emotional + rational hook
   - Media / press: newsworthy angle
   - Potential employees: purpose-driven pitch

Brand context:
- Company: [NAME]
- Category: [MARKET CATEGORY]
- Target customer: [ICP]
- Top 3 competitors: [LIST]
- Core differentiator: [WHAT ONLY YOU DO]""",
            ["brand", "positioning", "strategy", "messaging", "marketing"],
            389,
        ),
        (
            "Social Media Content Calendar Prompt",
            "Generate a week of on-brand social media content across LinkedIn, Twitter/X, and Instagram.",
            """You are a social media strategist. Create a 7-day content calendar for the brand described below.

For each day provide:
- Platform: LinkedIn / Twitter-X / Instagram
- Content type: educational / entertaining / promotional / community / behind-the-scenes
- Post copy (ready to publish, including emojis where appropriate)
- Hashtags (max 5, relevant)
- Best time to post (in the audience's timezone)
- Visual concept: describe the image or video in one sentence

Distribute: 3 educational, 2 community-building, 1 promotional, 1 behind-the-scenes.

Brand details:
- Brand: [NAME]
- Industry: [INDUSTRY]
- Audience: [AUDIENCE DESCRIPTION]
- Brand voice: [VOICE TRAITS: e.g. bold, witty, expert]
- Current campaign / theme: [THEME]""",
            ["social media", "content calendar", "LinkedIn", "Instagram", "content strategy"],
            356,
        ),
        (
            "Google Ads Copy Generator",
            "Write Google Search Ad copy that maximises click-through rate within character limits.",
            """You are a paid search specialist. Write Google Responsive Search Ad copy.

Deliver:
- 5 headlines (max 30 characters each) using these angles: keyword-match, benefit, CTA, social proof, urgency
- 4 description lines (max 90 characters each): expand benefits, handle objection, include CTA
- 2 callout extensions (max 25 characters each)
- 2 sitelink suggestions (link text + 2-line description each)

Optimisation rules:
- Include primary keyword in at least 2 headlines
- Use title case for headlines
- Avoid exclamation marks except in descriptions
- Every headline must make sense standalone

Ad details:
- Product/Service: [PRODUCT]
- Primary keyword: [KEYWORD]
- Landing page URL: [URL]
- Key differentiator: [DIFFERENTIATOR]
- Offer or promotion: [OFFER IF ANY]""",
            ["Google Ads", "PPC", "SEM", "ad copy", "paid search"],
            341,
        ),
    ],

    # ── Sales & Growth ──────────────────────────────────────────────────────
    "Sales & Growth": [
        (
            "B2B Cold Outreach Email",
            "Write a personalised, value-led cold outreach email that gets replies, not spam filters.",
            """You are an elite B2B sales development rep. Write a cold outreach email sequence (3 emails) to a target prospect.

Email 1 – The Hook (Day 1):
- Subject: personalised, curiosity-led, under 6 words
- Opening: 1 sentence of genuine personalisation (reference something real about their company)
- Bridge: connect their situation to a specific pain you solve
- Value: ONE concrete result a similar company achieved with you
- CTA: low-friction ask (15-minute call, not a demo)
- Length: max 100 words

Email 2 – The Value Add (Day 4):
- Lead with a useful insight/resource (not a sales pitch)
- One soft follow-up line

Email 3 – The Breakup (Day 10):
- Acknowledge they're busy, give them an easy out
- Leave the door open professionally

Prospect details:
- Company: [COMPANY]
- Title: [TITLE]
- Pain point: [PAIN]
- Your solution: [SOLUTION]
- Relevant case study: [CUSTOMER + RESULT]""",
            ["cold email", "outreach", "B2B", "SDR", "sales development"],
            598,
        ),
        (
            "Sales Discovery Call Script",
            "Run a structured discovery call that uncovers budget, authority, need, and timeline.",
            """You are a senior AE. Create a discovery call structure using the MEDDIC framework.

Structure:
1. Opening (2 min) – set the agenda, confirm time, build rapport
2. Situational questions (5 min) – understand their current state
3. Problem questions (5 min) – surface pain and quantify it
4. Implication questions (5 min) – expand the consequences of the problem
5. Need-payoff questions (3 min) – have them articulate the value of solving it
6. Qualification checkpoint (3 min) – MEDDIC: Metrics, Economic Buyer, Decision criteria, Decision process, Identify pain, Champion
7. Next steps (2 min) – always book the next meeting before hanging up

For each section provide:
- 3 example questions
- What to listen for
- Red/green flags

Prospect context:
- Industry: [INDUSTRY]
- Company size: [SIZE]
- Your solution: [SOLUTION]""",
            ["discovery call", "MEDDIC", "sales", "qualification", "B2B"],
            476,
        ),
        (
            "Objection Handling Playbook",
            "Turn the 7 most common sales objections into reasons to buy.",
            """You are a sales coach. Create a complete objection handling guide for the product below.

For each of the following objections, write:
- The real underlying concern (what they actually mean)
- An empathy acknowledgement (1 sentence, never argue)
- A reframe or clarifying question
- A value-anchored response (no more than 3 sentences)
- A proof point or social proof element

Objections to address:
1. "It's too expensive."
2. "We're already using [competitor]."
3. "We don't have budget right now."
4. "Send me some information and I'll get back to you."
5. "I need to talk to my team / get approval."
6. "Now is not a great time."
7. "We tried something similar before and it didn't work."

Product/Service: [YOUR PRODUCT]
Price point: [PRICE]
Top 3 competitors: [COMPETITORS]
Strongest differentiator: [DIFFERENTIATOR]""",
            ["objection handling", "sales", "negotiation", "closing", "pitch"],
            445,
        ),
        (
            "Value Proposition Canvas",
            "Build a sharp value proposition rooted in customer jobs, pains, and gains.",
            """You are a product marketing strategist. Complete a Value Proposition Canvas.

Customer Profile:
1. Customer jobs – list 5 functional, emotional, and social jobs your customer is trying to do
2. Customer pains – list 5 specific frustrations, risks, and obstacles they face today
3. Customer gains – list 5 outcomes and benefits they desire

Value Map:
4. Products & services – list exactly what you offer (be specific)
5. Pain relievers – for each pain, explain exactly how you relieve it (direct mapping)
6. Gain creators – for each gain, explain exactly how you create it (direct mapping)

Fit Analysis:
7. Identify the top 3 pain-reliever pairs (your biggest value drivers)
8. Write a one-sentence value proposition from this analysis

Company/Product: [PRODUCT]
Target segment: [SEGMENT]
Known customer research (if any): [RESEARCH/FEEDBACK]""",
            ["value proposition", "positioning", "product marketing", "customer research"],
            398,
        ),
        (
            "Account Expansion & Upsell Email",
            "Write a customer upsell email that feels helpful, not pushy.",
            """You are a Customer Success Manager writing an expansion email. This is NOT a cold email — the customer already loves your product.

Email structure:
- Subject: tied to a customer win or milestone, not a product name
- Opening: acknowledge a specific achievement they've had with your product (use data if possible)
- Bridge: connect that success to a natural next step / higher tier
- Value: 2–3 concrete outcomes the upgrade unlocks (their language, not feature language)
- Risk reversal: address the obvious objection (cost, migration, disruption)
- CTA: suggest a short call to 'explore if it makes sense' — low pressure
- Signature: personal, include your direct calendar link

Context:
- Customer name: [NAME]
- Current plan: [PLAN]
- Achievement to reference: [WIN / MILESTONE]
- Upgrade tier: [TIER]
- Key new capability: [CAPABILITY]""",
            ["upsell", "expansion", "customer success", "SaaS", "revenue"],
            367,
        ),
        (
            "Competitive Battle Card",
            "Build a concise battle card to win deals against your top competitor.",
            """You are a product marketing manager. Create a sales battle card for use in live competitive deals.

Sections:
1. Competitor overview (3 bullets: who they are, their ICP, their core message)
2. Where we win (3 scenarios where our solution is clearly better — with proof)
3. Where they win (be honest — 2 genuine competitor strengths)
4. Trap-setting questions (3 discovery questions that surface their weaknesses)
5. Landmines to avoid (phrases or discounts the competitor uses that we should pre-empt)
6. Best proof points against them (2 customer quotes or case study stats)
7. One-liner positioning against them

Our product: [OUR PRODUCT]
Competitor: [COMPETITOR NAME]
Competitor's main claim: [THEIR PITCH]
Our differentiator: [DIFFERENTIATOR]""",
            ["competitive", "battle card", "sales enablement", "win/loss", "positioning"],
            312,
        ),
    ],

    # ── Software Engineering ─────────────────────────────────────────────────
    "Software Engineering": [
        (
            "Code Review Checklist Generator",
            "Generate a thorough, language-specific code review checklist for your pull request.",
            """You are a principal engineer conducting a code review. Produce a structured code review checklist for the PR described below.

Checklist categories:
1. Correctness – does it do what it's supposed to?
2. Security – injection, authentication, authorisation, data exposure
3. Performance – N+1 queries, unnecessary computation, caching opportunities
4. Readability – naming, comments, complexity (cyclomatic), function length
5. Test coverage – edge cases, happy path, error path, mocking quality
6. API / Interface design – backward compatibility, versioning, documentation
7. Error handling – graceful degradation, logging, user-facing messages
8. Scalability – will this hold under 10× load?

For each item include:
- Specific question to ask
- What to look for
- Example of good vs. bad code pattern

PR context:
- Language / framework: [STACK]
- What the PR does: [DESCRIPTION]
- Performance requirements: [REQUIREMENTS]
- Any known constraints: [CONSTRAINTS]""",
            ["code review", "engineering", "PR", "quality", "best practices"],
            534,
        ),
        (
            "Technical Design Document (TDD)",
            "Draft a complete technical design document to align your team before writing a line of code.",
            """You are a staff engineer. Write a technical design document (TDD) for the feature described below.

Sections:
1. Summary – one paragraph describing what we're building and why
2. Motivation – problem statement, current limitations, user impact
3. Goals and non-goals – explicit list of both
4. High-level design – architecture diagram description, components involved
5. Detailed design – data models, API contracts, key algorithms, sequence diagrams (as text)
6. Alternatives considered – list 2–3 alternatives and why they were rejected
7. Security and privacy considerations
8. Performance and scalability plan
9. Rollout plan – feature flags, phased rollout, rollback strategy
10. Open questions – tag with owner and due date
11. Success metrics – how will we know this worked?

Feature: [FEATURE NAME]
Stack: [TECH STACK]
Team size: [SIZE]
Timeline: [DEADLINE]
Key constraints: [CONSTRAINTS]""",
            ["TDD", "design doc", "architecture", "engineering", "planning"],
            489,
        ),
        (
            "API Documentation Writer",
            "Generate complete, developer-friendly API documentation for any endpoint.",
            """You are a developer experience engineer. Write API documentation for the endpoint described below.

Include:
1. Endpoint overview – what it does in one sentence
2. Authentication – required headers/tokens
3. Request spec:
   - Method and URL
   - Path parameters (name, type, required, description)
   - Query parameters (name, type, required, default, description)
   - Request body schema (JSON with field descriptions)
4. Response spec:
   - 200/201 success schema with example
   - Error codes: 400, 401, 403, 404, 422, 429, 500 with example payloads
5. Rate limiting
6. curl example
7. JavaScript/Python code snippet
8. Changelog (version + what changed)

Endpoint details:
- Name: [ENDPOINT NAME]
- Method + path: [METHOD /path/{param}]
- Purpose: [WHAT IT DOES]
- Auth method: [JWT / API KEY / OAUTH]
- Request body: [DESCRIBE FIELDS]
- Response: [DESCRIBE RESPONSE]""",
            ["API", "documentation", "developer experience", "REST", "OpenAPI"],
            456,
        ),
        (
            "System Architecture Review",
            "Conduct a thorough architecture review and surface risks before they become incidents.",
            """You are a solutions architect. Conduct an architecture review for the system described below.

Review dimensions:
1. Reliability – SPOFs, failure modes, circuit breakers, retry logic
2. Security – attack surface, secret management, network segmentation, dependency vulnerabilities
3. Scalability – bottlenecks, horizontal scaling capability, database sharding strategy
4. Observability – logging, metrics, tracing, alerting coverage
5. Operational complexity – deployment pipeline, rollback, maintenance burden
6. Cost efficiency – resource utilisation, cost-per-transaction estimate
7. Technical debt – shortcuts taken, areas of entropy, prioritised refactoring list
8. Disaster recovery – RPO, RTO, backup strategy

For each dimension: current state assessment, risk rating (High/Medium/Low), specific recommendation.

System: [SYSTEM NAME]
Stack: [TECH STACK]
Scale: [REQUESTS PER DAY / DATA VOLUME]
Team size: [SIZE]
Known pain points: [PAIN POINTS]""",
            ["architecture", "system design", "infrastructure", "reliability", "scalability"],
            423,
        ),
        (
            "Incident Post-Mortem Writer",
            "Write a blameless post-mortem that drives real systemic improvements.",
            """You are an SRE writing a post-mortem report. Write a blameless post-mortem document.

Sections:
1. Incident summary – what happened, duration, impact (users affected, revenue lost, SLA breach)
2. Timeline – chronological sequence of events with timestamps (detection → diagnosis → mitigation → resolution)
3. Root cause analysis – use the 5 Whys technique, go to systemic causes not surface symptoms
4. Contributing factors – make it a list, include human, process, and technical factors
5. What went well – honest assessment of the response
6. What went poorly – process and tooling gaps
7. Action items – each with owner, due date, and priority (P0/P1/P2)
8. Metrics to track – how will we measure if the action items worked?

Incident details:
- Incident name/ID: [ID]
- Duration: [DURATION]
- Services affected: [SERVICES]
- Customer impact: [IMPACT]
- Summary of what happened: [NOTES]""",
            ["post-mortem", "incident", "SRE", "reliability", "blameless"],
            378,
        ),
        (
            "Refactoring Strategy Planner",
            "Plan a safe, incremental refactoring that modernises legacy code without breaking production.",
            """You are a senior software engineer tasked with refactoring legacy code. Create a refactoring strategy.

Deliverables:
1. Audit – identify code smells, anti-patterns, and technical debt hotspots
2. Risk map – rate each area by change frequency × complexity × test coverage
3. Strangler fig plan – how to incrementally replace the old code without big-bang rewrites
4. Test harness – what tests must exist BEFORE refactoring starts (characterisation tests)
5. Feature flag strategy – how to run old and new code in parallel
6. Rollback plan – what triggers a rollback and how to execute it safely
7. Sprint-by-sprint breakdown – 2-week increments with clear done criteria
8. Success metrics – code quality metrics before/after

System to refactor: [SYSTEM / MODULE]
Language/framework: [STACK]
Known issues: [ISSUES]
Test coverage today: [%]
Target timeline: [TIMELINE]""",
            ["refactoring", "legacy code", "technical debt", "engineering", "architecture"],
            334,
        ),
    ],

    # ── Data & Analytics ────────────────────────────────────────────────────
    "Data & Analytics": [
        (
            "Executive Data Story",
            "Transform raw numbers into a compelling narrative that drives decisions.",
            """You are a data storytelling expert. Transform the data provided into an executive-ready narrative.

Structure:
1. The headline insight – one sentence, the most important takeaway (not 'revenue grew by X%' but 'we are ahead of plan; growth is accelerating')
2. Context – what was the benchmark / prior period / target?
3. The 3-chart story – describe three charts (chart type, x-axis, y-axis, annotation) that tell the story visually
4. Causal analysis – what drove the results? Be specific.
5. Implication – so what? What decision does this enable?
6. Recommendation – one clear, actionable recommendation with owner and timeline

Tone: confident, direct, no hedging unless genuinely uncertain.

Data to work with:
[PASTE YOUR METRICS / TABLES HERE]

Audience: [EXECUTIVES / BOARD / TEAM]
Key decision to be made: [DECISION]""",
            ["data storytelling", "analytics", "executive", "visualisation", "insights"],
            445,
        ),
        (
            "A/B Test Hypothesis Generator",
            "Write a rigorous A/B test hypothesis with sample size calculation and success criteria.",
            """You are a growth analyst. Write a structured A/B test plan for the experiment described below.

Sections:
1. Hypothesis statement – "If we [change], then [metric] will [increase/decrease] by [X%] because [reason based on data/research]"
2. Metric(s) – primary metric, secondary metrics, guardrail metrics (must not worsen)
3. Audience – who is in the test, how are they segmented, what is excluded
4. Sample size calculation – based on baseline conversion rate, MDE, α=0.05, β=0.20 — show working
5. Duration estimate – given weekly traffic, how long to run
6. Implementation notes – what changes, what is the control
7. Decision criteria – p-value threshold, when to declare a winner, when to stop early
8. Risks – what could go wrong with this test

Experiment details:
- What you want to test: [CHANGE]
- Page/flow/feature: [WHERE]
- Current baseline conversion rate: [RATE]
- Minimum detectable effect: [MDE]
- Weekly eligible traffic: [TRAFFIC]""",
            ["A/B testing", "experimentation", "growth", "statistics", "CRO"],
            412,
        ),
        (
            "SQL Query Optimizer",
            "Analyse a slow SQL query and produce an optimised version with an explanation.",
            """You are a database performance engineer. Analyse the SQL query below and produce an optimised version.

For your response:
1. Diagnosis – explain why the original query is slow (missing indexes, full table scans, N+1 patterns, subquery inefficiency, etc.)
2. Optimised query – rewrite it with clear formatting and comments
3. Indexes to add – exact CREATE INDEX statements with reasoning
4. Execution plan comparison – describe what EXPLAIN ANALYZE would look like before vs. after
5. Further recommendations – query caching, pagination strategy, denormalisation if warranted
6. Edge cases – check for NULL handling, implicit type casting, timezone issues

Query to optimise:
[PASTE SQL HERE]

Database: [PostgreSQL / MySQL / BigQuery / etc.]
Table sizes (approximate):
[TABLE NAME]: [ROWS]
Current execution time: [TIME]
Peak load: [REQUESTS PER SECOND]""",
            ["SQL", "database", "performance", "query optimisation", "indexing"],
            389,
        ),
        (
            "KPI Dashboard Definition",
            "Define a complete set of KPIs for any business function with measurement methodology.",
            """You are a data strategy consultant. Build a KPI framework for the business function below.

For each KPI include:
1. KPI name (clear, jargon-free)
2. Business question it answers
3. Formula / calculation
4. Data source (table, API, tool)
5. Update frequency (real-time / daily / weekly / monthly)
6. Owner (role responsible for improving it)
7. Target (current baseline and 90-day goal)
8. Visualisation recommendation (chart type and key dimension to slice by)
9. Known data quality issues

Deliver:
- 3 North Star metrics (what matters most)
- 5–8 supporting operational metrics
- 2–3 leading indicators (predictive signals)

Business function: [FUNCTION e.g. Growth, Customer Success, Engineering, Finance]
Company stage: [STAGE]
Current tooling: [ANALYTICS STACK]""",
            ["KPIs", "metrics", "dashboard", "analytics", "data strategy"],
            356,
        ),
        (
            "Data Quality Audit Checklist",
            "Run a systematic data quality audit before trusting any dataset for decision-making.",
            """You are a data engineer conducting a data quality audit. Produce a comprehensive quality report for the dataset described.

Check each dimension:
1. Completeness – null rates per column, required fields missing
2. Uniqueness – duplicate record detection, primary key violations
3. Timeliness – data freshness, lag vs. source system
4. Consistency – cross-table referential integrity, conflicting values in related records
5. Validity – values within expected ranges/enumerations, type conformance
6. Accuracy – sample comparison to source of truth (manual spot-check)

For each dimension:
- Assessment methodology (SQL queries to run)
- Pass/fail threshold
- Current findings (if known)
- Remediation action

Dataset: [DATASET NAME]
Database/tool: [STACK]
Primary use case: [WHAT DECISIONS DOES THIS DATA POWER?]
Known issues: [ANY KNOWN PROBLEMS]""",
            ["data quality", "data engineering", "audit", "governance", "ETL"],
            298,
        ),
        (
            "Product Analytics Event Taxonomy",
            "Design a clean, future-proof analytics event taxonomy for any product.",
            """You are a product analytics architect. Design a complete event tracking taxonomy for the product below.

Deliverables:
1. Naming convention rules (verb_noun pattern, object_action vs action_object — pick one and justify)
2. Event categories:
   - Acquisition events (first-time user actions)
   - Activation events (aha-moment milestones)
   - Engagement events (core feature usage)
   - Retention events (habitual behaviours)
   - Revenue events (purchase, upgrade, renew)
   - Re-engagement events (return after dormancy)
3. For each event:
   - Event name
   - Trigger (exact UI action)
   - Properties (name, type, example value)
   - Business question it answers
4. Identity resolution strategy (anonymous → identified user merging)
5. Implementation notes (client-side vs. server-side, SDK)

Product: [PRODUCT NAME]
Core use case: [USE CASE]
Analytics tool: [MIXPANEL / AMPLITUDE / SEGMENT / GA4 / OTHER]""",
            ["product analytics", "event tracking", "analytics", "growth", "instrumentation"],
            267,
        ),
    ],

    # ── Productivity & Operations ───────────────────────────────────────────
    "Productivity & Operations": [
        (
            "OKR Writing Framework",
            "Write clear, ambitious OKRs that actually drive team alignment and accountability.",
            """You are an OKR coach. Write a complete OKR set for the team and period described.

For each Objective:
- Objective (aspirational, qualitative, memorable — makes people want to get out of bed)
- 3 Key Results:
  - Measurable and time-bound
  - Uses numbers not percentages where possible
  - Represents outcome, not output or activity
  - Graded 0.0–1.0 (0.7 is success — stretch goal)
- Owner
- Connection to company-level objective

Rules:
- 3–5 objectives maximum
- Every KR must have a clear measurement method
- Flag any KRs that are actually projects (milestones), not results

Team/function: [TEAM]
Company objective this flows from: [COMPANY OKR]
Quarter and year: [PERIOD]
Team's current priorities: [PRIORITIES]
Known constraints: [CONSTRAINTS]""",
            ["OKRs", "goal setting", "strategy", "management", "alignment"],
            478,
        ),
        (
            "Process Documentation Writer",
            "Document any business process in a clear, replicable SOP that any team member can follow.",
            """You are a business operations specialist. Write a Standard Operating Procedure (SOP) for the process described.

Format:
1. Process name and version
2. Purpose – why this process exists and what outcome it produces
3. Scope – what is included and excluded
4. Roles – who does what (RACI: Responsible, Accountable, Consulted, Informed)
5. Inputs required – what must exist before starting
6. Step-by-step procedure – numbered, imperative verbs, clear decision points marked with ⚡
7. Decision tree – if [condition], then [action] for the top 3 decision points
8. Outputs – what is produced and where it's stored
9. Exception handling – what to do when something goes wrong
10. Quality checkpoints – how to verify the process was done correctly
11. Revision history

Process to document: [PROCESS NAME]
Team: [TEAM]
Tools used: [TOOLS]
Approximate frequency: [DAILY / WEEKLY / AD HOC]""",
            ["SOP", "process documentation", "operations", "workflow", "templates"],
            412,
        ),
        (
            "Weekly Planning Prompt",
            "Plan your week with intention using a structured, high-performance planning routine.",
            """Guide me through a high-performance weekly planning session.

Walk me through these steps:

1. REVIEW LAST WEEK
   - What were my top 3 wins?
   - What didn't I finish and why?
   - What would I do differently?

2. CLARIFY THIS WEEK'S PRIORITIES
   - What are my 3 non-negotiable big rocks this week?
   - What are the top 5 tasks that will move the needle on my most important goal?

3. ENERGY MANAGEMENT
   - When is my peak focus time? Block 2-hour deep work sessions.
   - What meetings can be async? Push back on what can be an email.

4. PROACTIVE RISK MANAGEMENT
   - What is most likely to derail this week's plan?
   - What is my contingency?

5. WEEKLY THEME
   - What is the single most important thing I want to accomplish this week?
   - Write it as a personal commitment statement.

My context:
- Current top goal: [GOAL]
- Biggest project this week: [PROJECT]
- Known obstacles: [OBSTACLES]""",
            ["productivity", "planning", "time management", "personal development", "focus"],
            456,
        ),
        (
            "Decision Matrix Builder",
            "Make complex decisions objectively using a weighted scoring matrix.",
            """You are an executive decision coach. Help me build a weighted decision matrix for a complex choice.

Step 1 – Define the options: list all options being considered
Step 2 – Define criteria: what factors matter for this decision? (aim for 5–8)
Step 3 – Assign weights: total must equal 100%. Weight each criterion by importance.
Step 4 – Score each option 1–5 against each criterion (1=very poor, 5=excellent)
Step 5 – Weighted scores: multiply score × weight for each cell, sum the row
Step 6 – Sensitivity analysis: what changes if the top criterion weight is doubled?
Step 7 – Gut check: does the winning option feel right? If not, what criterion is missing?
Step 8 – Decision and rationale: state the decision with 3-sentence justification

Decision to make: [DESCRIBE THE DECISION]
Options under consideration: [LIST OPTIONS]
Most important factors: [YOUR CRITERIA]
Key constraint or non-negotiable: [CONSTRAINT]""",
            ["decision making", "strategy", "analysis", "management", "frameworks"],
            389,
        ),
        (
            "Retrospective Facilitator",
            "Facilitate a structured, psychologically safe team retrospective that produces real action items.",
            """You are an agile coach facilitating a team retrospective. Guide the team through a structured retro.

Framework: Start-Stop-Continue + Root Cause drilling

Phase 1 – Safety check (anonymous):
Generate 5 questions to quickly gauge team psychological safety

Phase 2 – Data gathering (15 min):
For each of START / STOP / CONTINUE, generate 3 powerful prompting questions to draw out honest responses

Phase 3 – Grouping and voting:
Instructions for clustering themes and dot-voting priorities

Phase 4 – Deep dive on top 2 items:
For each top item, apply the 5 Whys template to find the systemic root cause

Phase 5 – Action items:
Template for each action: What? Who? By when? How will we know it's done? (max 3 action items total)

Phase 6 – Closing:
One appreciations round + one-word check-out

Team context:
- Team size: [SIZE]
- Sprint length: [LENGTH]
- Biggest challenge this sprint: [CHALLENGE]
- Remote / in-person: [FORMAT]""",
            ["retrospective", "agile", "scrum", "team", "facilitation"],
            334,
        ),
        (
            "Meeting-Free Deep Work Scheduler",
            "Design a distraction-free schedule that protects time for high-impact focused work.",
            """You are a productivity architect. Design a weekly schedule that maximises deep work.

Principles to apply:
1. Time-block large chunks (minimum 90 minutes) for cognitively demanding work in peak energy windows
2. Batch all meetings into 2–3 meeting days using Cal Newport's bi-modal approach
3. Create a shutdown ritual that signals work end and protects recovery
4. Identify 3 recurring interruptions to eliminate or automate

Deliver:
- Annotated weekly template (Monday–Sunday, hourly blocks)
- Label each block: Deep Work / Shallow Work / Admin / Meeting / Recovery
- Rules for protecting deep work blocks (auto-responder language, Slack DND, etc.)
- 3 micro-habits that compound over time
- How to handle urgent interruptions without destroying focus

My context:
- Role: [ROLE]
- Core high-value work: [WHAT REQUIRES DEEP FOCUS]
- Current biggest time waster: [WASTER]
- Work hours preference: [HOURS]
- Meeting load today: [MEETINGS PER WEEK]""",
            ["deep work", "scheduling", "focus", "productivity", "time blocking"],
            298,
        ),
    ],

    # ── Content Creation ────────────────────────────────────────────────────
    "Content Creation": [
        (
            "Long-Form Blog Post Outline",
            "Build an SEO-optimised blog post outline that ranks and converts.",
            """You are a content strategist and SEO expert. Create a comprehensive blog post outline.

Outline structure:
1. Target keyword and search intent analysis (informational / transactional / navigational)
2. Title options (3 variations: SEO-optimised, curiosity-driven, list-based)
3. Meta description (155 characters, includes keyword, compelling CTA)
4. Introduction framework: hook → problem agitation → promise → roadmap
5. H2 sections (6–8) with:
   - Section purpose
   - Key points to make (3 bullets each)
   - Internal link opportunity
   - Supporting data or expert quote to find
6. Comparison table or visual element suggestion
7. FAQ section (5 questions based on 'People Also Ask')
8. Conclusion framework: summary → key takeaway → CTA
9. Internal and external link strategy
10. Suggested word count by section

Topic: [TOPIC]
Primary keyword: [KEYWORD]
Secondary keywords: [KEYWORDS]
Target audience: [AUDIENCE]
Funnel stage: [TOFU / MOFU / BOFU]""",
            ["SEO", "blog", "content marketing", "writing", "organic traffic"],
            478,
        ),
        (
            "LinkedIn Thought Leadership Post",
            "Write a LinkedIn post that builds authority, earns engagement, and grows your following.",
            """You are a LinkedIn content strategist who has grown accounts to millions of followers.

Write a LinkedIn post using the following formula:
1. HOOK (line 1, visible before 'see more'): counter-intuitive statement, surprising stat, or bold opinion — make stopping mandatory
2. BRIDGE (lines 2–3): acknowledge the conventional wisdom you're about to challenge
3. CORE (lines 4–12): your unique insight or framework, formatted with line breaks for scannability, numbered lists or short paragraphs
4. STORY or PROOF (2–3 lines): personal experience, case study, or data that validates your point
5. TAKEAWAY: one memorable, rephrasing of the insight they can use today
6. CTA: ask a genuine question to drive comments OR tell them what to do next

Rules:
- No hashtags in the body — max 3 at the end
- Emojis sparingly (0–2 max)
- Each line max 8 words
- Avoid corporate jargon

Topic: [TOPIC]
Your unique angle: [ANGLE]
Target audience: [AUDIENCE]
Your experience/credibility: [CREDIBILITY]""",
            ["LinkedIn", "thought leadership", "personal brand", "content", "B2B"],
            456,
        ),
        (
            "YouTube Video Script",
            "Write a YouTube video script with a hook that holds attention and drives watch time.",
            """You are a YouTube scriptwriter. Write a complete video script.

Structure:
1. HOOK (0:00–0:30): open with a bold promise, provocative question, or surprising reveal — no slow intro, no 'hey guys'
2. CREDIBILITY (0:30–1:00): why should they listen to you? (keep it brief, not boastful)
3. ROADMAP (1:00–1:30): tell them what they'll learn — this reduces drop-off
4. CHAPTERS (3–5 main points): each chapter:
   - Title card text
   - Core teaching (clear and specific)
   - Example or demonstration
   - Transition hook to next chapter ('but here's where most people get it wrong...')
5. CALL TO ACTION (last 60 seconds): subscribe, comment, next video — pick ONE
6. END SCREEN PROMPT: what related video to watch next

Formatting: write as-spoken, colloquial, with [B-ROLL] notes and [PAUSE] cues

Video topic: [TOPIC]
Target audience: [AUDIENCE]
Video length target: [MINUTES]
Main transformation: [WHAT THEY'LL BE ABLE TO DO AFTER]""",
            ["YouTube", "video script", "content creation", "video marketing", "SEO"],
            423,
        ),
        (
            "Email Newsletter Issue",
            "Write a newsletter issue people actually look forward to reading.",
            """You are the editor of a top-tier industry newsletter. Write a complete newsletter issue.

Structure:
1. Subject line and preview text (pair them for max open rate)
2. OPENING: personal, anecdote-led hook (3–5 sentences), sets up the issue theme
3. MAIN STORY (400–600 words):
   - Intriguing headline
   - The story: what happened, why it matters, what others missed
   - Your unique take / analysis
   - 1 concrete implication for the reader
4. QUICK HITS: 3 links/stories with 1-sentence why-it-matters commentary each
5. TOOL OF THE WEEK: one useful tool, app, framework (name, what it does, why you like it)
6. CLOSING THOUGHT: 2–3 sentence reflection that ties back to the opening theme
7. CTA: one action (reply, fwd, sponsor slot, paid tier upsell)

Newsletter details:
- Name and niche: [NAME, NICHE]
- Audience: [AUDIENCE]
- Issue theme: [THEME]
- Main story: [STORY OR TOPIC]
- Tone: [VOICE]""",
            ["newsletter", "email", "content", "audience building", "media"],
            389,
        ),
        (
            "Podcast Episode Outline",
            "Plan a podcast episode that keeps listeners engaged and positions your guest perfectly.",
            """You are a podcast producer. Create a complete episode plan including interview guide.

Episode structure:
1. Episode title (3 options: curiosity-gap, benefit-led, name-drop)
2. Episode description (2 sentences, includes searchable keywords)
3. Pre-show research checklist (5 things to know about the guest before recording)
4. Opening script (host reads verbatim): tease the insight, intro the guest compellingly
5. Interview arc (4 phases with time allocation):
   - Origin story: how they got here (5 min)
   - Conventional wisdom challenge: what they believe that most people don't (10 min)
   - Deep dive: the core lesson/framework (15–20 min)
   - Rapid fire + close: rapid-fire questions + what's next for them (5 min)
6. Question bank (20 questions, mark the top 10 as must-ask)
7. Sponsorship insertion points
8. Outro script with CTA (subscribe, review, newsletter)

Guest: [GUEST NAME & TITLE]
Guest expertise: [EXPERTISE]
Key story you want to draw out: [STORY]
Episode theme: [THEME]""",
            ["podcast", "content", "interview", "audio", "media production"],
            312,
        ),
        (
            "Case Study Writer",
            "Write a compelling customer case study that converts prospects.",
            """You are a product marketing writer. Write a customer case study.

Structure:
1. HEADLINE: [Customer name] + [Result] in [timeframe] — lead with the outcome
2. EXECUTIVE SUMMARY (3 sentences): who the customer is, what they did, what they achieved
3. THE CHALLENGE:
   - Customer context (industry, size, key details)
   - The specific problem they faced (in their words)
   - What they tried before (and why it failed)
   - Business impact of the problem (lost revenue, wasted time, risk)
4. THE SOLUTION:
   - Why they chose us (quote from the decision maker)
   - How they implemented it (timeline, process)
   - Who was involved
5. THE RESULTS:
   - 3 headline metrics (quantified)
   - Qualitative benefit (quote from end user)
   - ROI calculation
6. WHAT'S NEXT: their future plans with your product

Customer details:
- Company: [COMPANY]
- Industry: [INDUSTRY]
- Challenge: [CHALLENGE]
- Solution used: [YOUR PRODUCT / FEATURE]
- Key results: [METRICS]
- Decision maker quote (if available): [QUOTE]""",
            ["case study", "social proof", "marketing", "content", "conversion"],
            278,
        ),
    ],

    # ── Legal & Compliance ──────────────────────────────────────────────────
    "Legal & Compliance": [
        (
            "Contract Risk Clause Analyser",
            "Identify and explain the highest-risk clauses in any commercial contract.",
            """You are an experienced commercial lawyer reviewing a contract. Analyse the contract excerpt below and provide a risk assessment.

For each risk identified:
1. Clause location (section number if available)
2. Risk type: financial / reputational / operational / legal
3. Risk severity: High / Medium / Low with justification
4. Plain-English explanation of what the clause means
5. Negotiation recommendation: accept / modify / reject
6. Suggested alternative language (if modify)
7. Red flag checklist: flag any of these: unlimited liability, unilateral change rights, broad IP assignment, auto-renewal clauses, non-compete/non-solicit scope, unreasonable termination clauses

Also provide:
- Overall risk rating: High / Acceptable / Low
- Top 3 clauses to negotiate first
- Questions to ask the other party's counsel

Contract text:
[PASTE CONTRACT EXCERPT HERE]

Your role: [BUYER / SELLER / EMPLOYER / OTHER]
Contract type: [MSA / SaaS / EMPLOYMENT / NDA / OTHER]""",
            ["contract", "legal", "risk", "compliance", "due diligence"],
            345,
        ),
        (
            "Privacy Policy Section Drafter",
            "Draft GDPR and CCPA-compliant privacy policy sections in plain, user-friendly language.",
            """You are a privacy lawyer. Draft a privacy policy section that is legally compliant and readable.

Requirements:
- GDPR compliant (for EU/EEA users)
- CCPA compliant (for California users)
- Written at a 8th-grade reading level — no legalese
- Cover the specific section requested
- Include a 'Summary Box' at the top of each section (3 bullets of what they need to know)
- Flag any areas where exact details are needed (in [BRACKETS])

Sections to draft (specify which ones):
- Data we collect
- How we use your data
- Data retention
- Your rights
- Cookies policy
- Third-party sharing
- Data transfers (international)
- Contact and complaints

Company details:
- Company name: [NAME]
- Country of incorporation: [COUNTRY]
- Services provided: [SERVICES]
- Data you collect: [DATA TYPES]
- Third parties you share with: [LIST]
- DPO or privacy contact: [CONTACT]""",
            ["privacy policy", "GDPR", "CCPA", "legal", "compliance"],
            312,
        ),
        (
            "NDA Plain-English Explainer",
            "Translate any NDA into plain English, highlighting what you're agreeing to.",
            """You are a contracts paralegal. Review the NDA provided and explain it in plain English.

For each major clause:
1. What it says (one sentence summary)
2. What it means for you practically
3. Duration of obligation
4. Your exposure if breached (estimate high/medium/low)
5. Is this standard? Flag anything unusual.

Summary analysis:
- What information is covered by the NDA?
- What are you ALLOWED to disclose and to whom?
- What are the key obligations?
- How long does the NDA last?
- What happens if you accidentally disclose?
- How do you exit the NDA?

Flags to check:
□ Is the definition of confidential information too broad?
□ Are there carve-outs for publicly available information?
□ Is the non-solicitation clause included (and is it reasonable)?
□ Is the governing law / jurisdiction acceptable?

NDA text:
[PASTE NDA TEXT HERE]""",
            ["NDA", "legal", "contracts", "confidentiality", "plain English"],
            278,
        ),
        (
            "GDPR Data Processing Record",
            "Create a GDPR Article 30 record of processing activities for any product or team.",
            """You are a Data Protection Officer. Create a Records of Processing Activities (RoPA) entry compliant with GDPR Article 30.

For each processing activity, document:
1. Name and description of processing activity
2. Controller details (company, DPO contact)
3. Purposes of processing
4. Legal basis (consent / contract / legitimate interest / legal obligation / vital interests / public task)
5. If legitimate interest: complete the 3-part LIA test
6. Categories of data subjects
7. Categories of personal data
8. Categories of recipients
9. International transfers (third countries, safeguards used)
10. Retention periods (per data category)
11. Technical and organisational security measures

Then produce:
- Data flow diagram description (text-based)
- Risk rating (High / Medium / Low) and justification
- Recommended Data Protection Impact Assessment (DPIA) required? Yes/No + reason

Processing activity to document: [ACTIVITY]
Company: [COMPANY]
Tech stack involved: [SYSTEMS]""",
            ["GDPR", "data protection", "DPO", "compliance", "privacy"],
            245,
        ),
        (
            "Employment Contract Clause Drafter",
            "Draft fair, enforceable employment contract clauses for key provisions.",
            """You are an employment lawyer. Draft the following employment contract clause(s).

For each clause:
1. Draft the clause in clear, enforceable language
2. Note jurisdiction-specific considerations
3. Flag any provisions that may be unenforceable in common jurisdictions
4. Provide a 'softer' variant (more employee-friendly) and a 'harder' variant (more employer-protective)
5. Plain-English summary of what both parties are agreeing to

Clauses to draft (specify):
- Non-compete (duration, geography, scope)
- Non-solicitation (employees and customers)
- Intellectual property assignment
- Confidentiality (during and post-employment)
- At-will employment / termination notice
- Arbitration clause
- Garden leave provision

Employee details:
- Role: [ROLE]
- Seniority level: [LEVEL]
- Access to sensitive data: [YES / NO]
- Non-compete duration requested: [DURATION]
- Primary jurisdiction: [COUNTRY / STATE]""",
            ["employment law", "contracts", "HR", "compliance", "legal"],
            212,
        ),
        (
            "Terms of Service Drafter",
            "Draft clear, enforceable Terms of Service for any SaaS product.",
            """You are a tech startup lawyer. Draft a Terms of Service agreement for the product below.

Required sections:
1. Acceptance of terms
2. Description of service
3. User accounts (eligibility, account security, termination)
4. Acceptable use policy (what users can and cannot do)
5. Intellectual property (who owns what — user content vs. platform)
6. Subscription and payments (auto-renewal, refunds, price changes)
7. Limitation of liability (cap and exclusions)
8. Warranty disclaimer
9. Indemnification
10. Dispute resolution (arbitration vs. litigation, governing law)
11. Changes to these terms
12. Contact information

For each section:
- Plain-English summary box
- The actual clause in legal language
- Note any state/country-specific variations

Product details:
- Product name: [PRODUCT]
- Service type: [B2B SAAS / B2C APP / MARKETPLACE]
- Country of incorporation: [COUNTRY]
- User-generated content? [YES / NO]
- Subscription model? [YES / NO + DETAILS]""",
            ["terms of service", "legal", "SaaS", "compliance", "contracts"],
            198,
        ),
    ],

    # ── HR & Recruiting ─────────────────────────────────────────────────────
    "HR & Recruiting": [
        (
            "Job Description Writer",
            "Write a compelling job description that attracts A-players and filters out mismatches.",
            """You are a talent acquisition specialist. Write a job description that attracts exceptional candidates.

Structure:
1. Title (clear, searchable, no internal jargon)
2. TL;DR Summary (3 sentences: what you'll do, what you'll build, why it matters)
3. The opportunity (why this role is exciting — company mission, product, team)
4. What you'll do (5–8 bullets, outcome-focused, use 'you will…' not 'responsibilities include')
5. Who you are (5 must-haves, 3 nice-to-haves — keep the bar high but realistic)
6. What we offer (comp range, equity, benefits — be transparent)
7. Our hiring process (every step, timeline — remove ambiguity)
8. Inclusivity statement (genuine, not boilerplate)

Anti-patterns to avoid:
- 'Wear many hats' (meaningless)
- 10+ years experience for clearly mid-level roles
- Long laundry lists of 'requirements' that are actually preferences
- Vague adjectives: 'dynamic', 'passionate', 'rockstar'

Role details:
- Title: [TITLE]
- Team: [TEAM]
- Seniority: [LEVEL]
- Comp range: [COMPENSATION]
- Must-have skills: [SKILLS]
- Top 3 deliverables in year 1: [DELIVERABLES]""",
            ["recruiting", "job description", "talent", "HR", "hiring"],
            478,
        ),
        (
            "Structured Interview Guide",
            "Build a structured interview guide with behavioural questions that predict job performance.",
            """You are a talent assessment expert. Build a structured interview guide.

Principles:
- Use STAR format for all behavioural questions (Situation, Task, Action, Result)
- Match questions to specific competencies
- Include 'probe' follow-up questions to go deeper
- Provide a scoring rubric (1–5) for each question

Guide components:
1. Role overview briefing for interviewers (2 min read)
2. Interview structure (phases + time allocation)
3. Rapport opener (non-evaluative, sets psychological safety)
4. Competency-based questions (6–8 questions mapped to the top competencies for this role):
   - Behavioural question
   - What a 1 (poor), 3 (acceptable), 5 (exceptional) answer looks like
   - 2 probe follow-ups
5. Technical/situational questions (3–4 role-specific scenarios)
6. Candidate's questions section (what to listen for)
7. Debrief scorecard template

Role: [ROLE]
Key competencies: [COMPETENCIES e.g. problem-solving, leadership, execution]
Stage: [PHONE SCREEN / 1ST ROUND / FINAL]""",
            ["interview", "recruiting", "hiring", "assessment", "HR"],
            445,
        ),
        (
            "Onboarding Plan Creator",
            "Design a 30-60-90 day onboarding plan that ramps new hires to full productivity fast.",
            """You are a people operations manager. Create a 30-60-90 day onboarding plan.

Structure for each phase:

DAYS 1–30 – Learn:
- Priority: understand the business, the team, and the role
- Week 1 must-dos (technical setup, key stakeholder meetings, systems access)
- Meetings to schedule (with whom and purpose)
- Documents and resources to consume
- First deliverable (low-stakes, high-visibility win)

DAYS 31–60 – Contribute:
- Start owning defined areas
- Projects to lead or co-lead
- Feedback checkpoint (manager + peers)
- Success metric: what does 'on track' look like?

DAYS 61–90 – Lead:
- Fully independent execution
- First significant deliverable
- 90-day review criteria and self-assessment
- What does 'exceptional' look like vs. 'meeting expectations'?

Include:
- Manager commitment (what manager must do)
- Buddy/mentor plan
- Cultural integration checklist

Role: [ROLE]
Team: [TEAM]
Key systems to learn: [SYSTEMS]
First project: [PROJECT]""",
            ["onboarding", "HR", "new hire", "management", "people operations"],
            412,
        ),
        (
            "Performance Improvement Plan (PIP)",
            "Write a fair, legally sound PIP that gives employees a genuine opportunity to improve.",
            """You are an HR business partner. Write a Performance Improvement Plan.

PIP structure:
1. Purpose statement (supportive, not punitive tone)
2. Background: performance expectations vs. current performance (factual, specific)
3. Performance gaps: 3–5 specific, observable, measurable gaps
4. For each gap:
   - Current observed behaviour (with date and specific example)
   - Expected behaviour and standard
   - Improvement objective (SMART)
   - Resources and support provided (training, coaching, tools)
   - Measurement method (how will we assess improvement?)
5. Timeline (typically 30/60/90 days with checkpoints)
6. Check-in schedule (frequency, format, attendees)
7. Consequences of non-improvement (stated clearly and professionally)
8. Employee acknowledgement section

Principles:
- Every gap must have a specific example
- Every objective must be achievable in the PIP timeframe
- Resources offered must be genuine

Employee context:
- Role: [ROLE]
- Performance issues: [ISSUES]
- Prior feedback given: [FEEDBACK HISTORY]
- Timeline: [30 / 60 / 90 DAYS]""",
            ["PIP", "performance", "HR", "management", "employee relations"],
            356,
        ),
        (
            "Candidate Rejection Email",
            "Write a rejection email that is kind, specific, and protects your employer brand.",
            """You are a recruiter. Write a candidate rejection email for the three stages below.

For each stage write a template:

1. APPLICATION STAGE rejection (no interview):
   - Acknowledge receipt, thank for time
   - Brief, honest reason (if possible)
   - Encourage future applications if appropriate

2. POST-INTERVIEW rejection (1st or 2nd round):
   - Warm, personal opener
   - Recognise their strengths specifically
   - Honest reason without disparaging company or other candidates
   - Leave the door open if appropriate
   - Offer brief feedback (optional checkbox at bottom)

3. FINAL ROUND rejection (they made it to the last step):
   - Acknowledge courage and investment
   - Specific strengths observed
   - Honest reason — it was a close decision
   - Offer a 15-minute feedback call
   - Proactively refer them to other roles or their network

Rules for all:
- Never say 'you'll be kept on file' unless you mean it
- No form-letter openers ('We regret to inform you')
- Match the warmth to the depth of the interview process

Role applied for: [ROLE]
Stage: [STAGE]
Candidate name: [NAME]""",
            ["recruiting", "candidate experience", "HR", "employer brand", "email"],
            312,
        ),
        (
            "Employee Engagement Survey",
            "Design a high-response-rate engagement survey that surfaces what employees actually think.",
            """You are an organisational psychologist. Design an employee engagement survey.

Survey principles:
- 15–25 questions maximum (respects time, increases completion)
- Mix of Likert scale (1–5) and open-text for richness
- Questions measure drivers, not just outcomes
- Anonymous design philosophy

Question categories:
1. Role clarity & meaning (3 questions)
2. Manager relationship (3 questions)
3. Team collaboration (2 questions)
4. Growth & development (3 questions)
5. Recognition & appreciation (2 questions)
6. Company direction & trust (3 questions)
7. Workload & wellbeing (3 questions)
8. Net Promoter (1 eNPS question + 1 open follow-up)
9. Open feedback (1 question: 'What is one thing we should start/stop/continue doing?')

For each question:
- The question (clear, single-concept, no leading language)
- Response format
- Which engagement driver it measures
- How to action low scores for this question

Company context:
- Size: [SIZE]
- Industry: [INDUSTRY]
- Current biggest concern: [CONCERN]""",
            ["engagement", "HR", "employee survey", "culture", "people ops"],
            278,
        ),
    ],

    # ── Customer Success ────────────────────────────────────────────────────
    "Customer Success": [
        (
            "Customer Onboarding Email Sequence",
            "Write a 5-email onboarding sequence that gets customers to their first value moment fast.",
            """You are a customer success manager. Write a 5-email onboarding sequence timed to drive activation.

Email 1 – Welcome (send immediately after sign-up):
- Warm welcome from a real person (not 'the team')
- The ONE thing they should do first (single CTA)
- Response encouraged

Email 2 – First Value Prompt (Day 2):
- 'Have you tried [key feature]?' — guide them to the aha moment
- 2-step tutorial (keep it  under 3 minutes)
- Social proof: 'Customers who do X see Y result'

Email 3 – Use Case Deepener (Day 5):
- Share one expert tip tied to their likely use case
- Invite to a live onboarding webinar or 1:1 call

Email 4 – Engagement Check (Day 10):
- Personal check-in — have they hit their first milestone?
- Celebrate progress if they have, offer help if not
- 'Reply to this email' CTA to drive conversation

Email 5 – 30-Day Value Review (Day 28):
- Recap of what they've done and the value created (pull from product data if possible)
- Introduce next-level features
- Soft upsell to higher tier (if applicable)

Product: [PRODUCT]
Core aha moment: [AHA MOMENT]
Target persona: [PERSONA]""",
            ["onboarding", "customer success", "email sequence", "activation", "SaaS"],
            512,
        ),
        (
            "Quarterly Business Review (QBR) Agenda",
            "Design a QBR that customers actually value and that surfaces expansion opportunities.",
            """You are a senior CSM. Create a QBR agenda and talking points for the account below.

QBR structure (90-minute format):

1. OPENER (5 min) – set collaborative tone, confirm agenda and time
2. CUSTOMER UPDATE (10 min) – what's changed for them since last QBR (strategy, team, goals)
3. MUTUAL SUCCESS REVIEW (20 min):
   - Goals set last QBR vs. results achieved
   - Product adoption metrics (key features used, user counts, frequency)
   - Business outcomes tied to product usage (their KPIs, not our metrics)
4. CHALLENGES & ROADBLOCKS (10 min) – open forum, psychological safety needed
5. STRATEGIC ROADMAP (15 min) – what's coming from our side that matters to them
6. JOINT SUCCESS PLAN (20 min) – set 3–5 goals for next quarter with owners and dates
7. COMMERCIAL REVIEW (5 min) – NPS discussion, renewal/expansion conversation if appropriate
8. CLOSE (5 min) – send-away insight, thank you, action items recap

Account details:
- Customer: [CUSTOMER]
- CSM: [YOUR NAME]
- Key business goals: [GOALS]
- Adoption challenges: [CHALLENGES]
- Expansion opportunity: [OPPORTUNITY]""",
            ["QBR", "customer success", "account management", "retention", "B2B"],
            478,
        ),
        (
            "Churn Risk Intervention Email",
            "Write a churn-prevention email that re-engages at-risk customers before it's too late.",
            """You are a CSM who has just identified a customer at risk of churning. Write a re-engagement email.

Email must:
- Not mention 'we noticed you haven't logged in' (creepy) — instead reference a business outcome
- Lead with value to them, not concern for your revenue
- Be short (under 150 words)
- Have one specific CTA
- Feel 1:1 not automated (use merge fields, feel personal)

Structure:
- Subject: [Outcome-focused, not 'checking in' — 3 options]
- Opening: reference their stated goal or use case (not a product action)
- Bridge: one valuable insight or resource tied to that goal
- Offer: low-friction action (15-min call, new tutorial, or feature they haven't tried)
- Closing: warm, no pressure

Also write:
- A follow-up (if no reply in 5 days): acknowledge the silence, give an easy out ('happy to close this chain')
- An internal note to the AE: what the risk signal is and the recommended next step

Customer: [NAME]
Risk signal: [SIGNAL] (e.g. low login frequency, support tickets, champion left)
Their stated goal at onboarding: [GOAL]""",
            ["churn", "retention", "customer success", "email", "SaaS"],
            445,
        ),
        (
            "NPS Detractor Recovery Script",
            "Turn your unhappiest customers into advocates with a structured recovery conversation.",
            """You are a VP of Customer Success. Design a detractor recovery process for customers who gave NPS 0–6.

Recovery framework:

1. Pre-call research (before picking up the phone):
   - List 5 things to review: support tickets, feature usage, CSAT scores, contract renewal date, champion info

2. Outreach message (text/email to book the call):
   - Short, genuine, no defensiveness
   - Acknowledge the score, not the number ('we know we've fallen short')
   - Ask for 20 minutes to listen

3. Discovery call structure:
   - Opening: thank them for honesty, commit to listening
   - Probe: 'Can you walk me through the moment things started going wrong?'
   - Root cause questions (5 follow-up probes)
   - Silence strategy: let them finish fully before responding

4. Live recovery response (in the call):
   - Acknowledge (repeat back what you heard)
   - Own it (no excuses, even if the issue is partly their fault)
   - Commit (specific action, owner, timeline)

5. Follow-up email (within 24 hours): recap commitments, next check-in date

6. 30-day check-in: how to measure if the recovery worked

Customer details:
- NPS score: [SCORE]
- Reason given: [VERBATIM COMMENT]
- Account value: [TIER]""",
            ["NPS", "customer success", "recovery", "retention", "CSAT"],
            412,
        ),
        (
            "Customer Success Business Case",
            "Build a ROI business case that helps your champion get internal buy-in for renewal or expansion.",
            """You are a CSM building a business case for your champion to share with their CFO.

Business case structure:
1. Executive summary (1 page) – investment vs. return in their language
2. Problem statement – what they were dealing with before (quantified in their own KPIs)
3. Solution deployed – what they actually use (not a product feature list — outcomes only)
4. Value delivered:
   - Time saved (hours/week × headcount × fully-loaded cost)
   - Revenue generated or protected (with methodology)
   - Cost avoided (what they would have had to hire/build otherwise)
   - Risk reduction (harder to quantify — use a range)
5. ROI calculation: Total Value / Annual Contract Value = ROI%
6. Payback period
7. Intangibles (competitive advantage, employee satisfaction, scalability)
8. Next-phase opportunity: what additional value they could unlock
9. Risks of not renewing / expanding

Format as an executive brief they can present verbatim.

Customer: [CUSTOMER]
ACV: [ANNUAL CONTRACT VALUE]
Usage data: [KEY STATS]
Their top priority: [PRIORITY]""",
            ["ROI", "business case", "customer success", "renewal", "expansion"],
            378,
        ),
        (
            "Customer Success Story Interview Script",
            "Conduct a customer interview that extracts a compelling case study.",
            """You are a content marketer conducting a customer success story interview. Create a complete interview guide.

Pre-interview:
- 5 things to research before the call
- Release form / approval checklist
- How to frame the purpose of the interview to the customer

Interview structure (45 minutes):

WARMUP (5 min):
- 3 rapport-building questions (their role, how long with product, casual opener)

BEFORE STATE (10 min):
- What was the problem before?
- How were you handling it?
- What was the business impact? (probe for numbers)
- Why did the old way no longer work?

DECISION (5 min):
- How did you find us?
- What made you choose us over alternatives?

AFTER STATE (15 min):
- Walk me through how you use it now
- What result are you most proud of? (probe for specific metrics)
- What surprised you?
- What would you tell a peer considering this?

SNACKABLE QUOTES (5 min):
- 'If you had to describe the value in one sentence…'
- 'What headline would you write about the results?'

CLOSE (5 min):
- Permission to quote/use story
- Preferred company description for attribution

Customer: [CUSTOMER]
Product used: [PRODUCT]
Expected headline result: [RESULT]""",
            ["case study", "customer story", "interview", "social proof", "content"],
            334,
        ),
    ],
}

# ---------------------------------------------------------------------------


class Command(BaseCommand):
    help = (
        "Seed the database with 60 professional plain-text prompts across 10 "
        "high-monetisation categories. Idempotent — safe to run multiple times."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be created without touching the database.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all templates previously created by this command before re-seeding.",
        )
        parser.add_argument(
            "--category",
            type=str,
            default=None,
            help="Only seed prompts for this specific category name.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        clear = options["clear"]
        target_category = options.get("category")

        self.stdout.write(self.style.MIGRATE_HEADING("🚀  PromptCraft Pro Prompt Inflator"))

        admin_user = self._get_or_create_admin_user()

        if clear and not dry_run:
            deleted, _ = Template.objects.filter(
                performance_metrics__source="inflate_pro_prompts"
            ).delete()
            self.stdout.write(self.style.WARNING(f"🗑  Cleared {deleted} existing pro prompts."))

        created_total = 0
        skipped_total = 0

        categories_to_run = (
            {target_category: PRO_PROMPTS[target_category]}
            if target_category and target_category in PRO_PROMPTS
            else PRO_PROMPTS
        )

        with transaction.atomic():
            for cat_name, prompts in categories_to_run.items():
                cat_meta = CATEGORIES[cat_name]
                category_obj = self._get_or_create_category(
                    cat_name, cat_meta, dry_run
                )

                for title, description, content, tags, use_count in prompts:
                    created, skipped = self._upsert_template(
                        title=title,
                        description=description,
                        content=content,
                        tags=tags,
                        use_count=use_count,
                        category=category_obj,
                        author=admin_user,
                        dry_run=dry_run,
                    )
                    created_total += created
                    skipped_total += skipped

        verb = "Would create" if dry_run else "Created"
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅  {verb} {created_total} prompts  |  Skipped {skipped_total} duplicates\n"
            )
        )

    # ------------------------------------------------------------------ utils

    def _get_or_create_admin_user(self):
        user, created = User.objects.get_or_create(
            username="promptcraft_admin",
            defaults={
                "email": "admin@promptcraft.app",
                "is_staff": True,
                "first_name": "PromptCraft",
                "last_name": "Admin",
            },
        )
        if created:
            user.set_unusable_password()
            user.save()
            self.stdout.write(f"👤  Created system user: {user.username}")
        return user

    def _get_or_create_category(self, name, meta, dry_run):
        from apps.templates.models import TemplateCategory
        if dry_run:
            self.stdout.write(f"  [DRY-RUN] Category: {name}")
            return None
        cat, created = TemplateCategory.objects.get_or_create(
            name=name,
            defaults={
                "slug": slugify(name),
                "icon": meta["icon"],
                "color": meta["color"],
                "order": meta["order"],
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"  📁  Created category: {name}")
        return cat

    def _upsert_template(
        self, title, description, content, tags, use_count, category, author, dry_run
    ):
        from apps.templates.models import Template
        if dry_run:
            self.stdout.write(f"    [DRY-RUN] {title}")
            return 1, 0

        obj, created = Template.objects.get_or_create(
            title=title,
            category=category,
            defaults={
                "description": description,
                "template_content": content,
                "author": author,
                "tags": tags,
                "usage_count": use_count,
                "is_public": True,
                "is_active": True,
                "is_featured": False,
                "version": "1.0.0",
                "performance_metrics": {"source": "inflate_pro_prompts"},
            },
        )
        if created:
            self.stdout.write(f"    ✅  {title}")
            return 1, 0
        else:
            # Silently skip duplicates
            return 0, 1
