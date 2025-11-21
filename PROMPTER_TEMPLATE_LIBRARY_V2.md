# Prompter Template Library - Production Templates

## Template System Architecture

This library contains 100+ production-ready templates organized by category and optimized for maximum user value with minimal input requirements.

### Template Categories

1. **Software Development** (25 templates)
2. **Business & Marketing** (20 templates) 
3. **Creative & Content** (15 templates)
4. **Productivity & Automation** (15 templates)
5. **Specialized Industries** (25 templates)

---

## SOFTWARE DEVELOPMENT TEMPLATES (25)

### 1. Complete SaaS Application Builder
**ID**: `saas_builder_complete`
**Category**: software_development
**Priority**: 1
**Use Case**: Create full-stack applications

```json
{
  "id": "saas_builder_complete",
  "name": "Complete SaaS Application Builder",
  "category": "software_development",
  "surfaces": ["chatgpt", "claude", "generic"],
  "useCase": "development",
  "priority": 1,
  "variables": {
    "BUSINESS_TYPE": "e.g., project management, CRM, analytics",
    "TECH_STACK": "React/Node.js, Python/Django, etc.",
    "DEPLOYMENT": "AWS, Vercel, Docker, etc.",
    "FEATURES": "core functionality list"
  },
  "template": {
    "role": "Act as a senior full-stack architect and SaaS product manager with 10+ years experience building scalable applications.",
    "context": "Create a complete, production-ready {BUSINESS_TYPE} SaaS application that can be deployed and monetized within 24-48 hours.",
    "inputs": [
      "Business type: {BUSINESS_TYPE}",
      "Preferred tech stack: {TECH_STACK}",
      "Deployment target: {DEPLOYMENT}",
      "Core features needed: {FEATURES}",
      "Target user base size: {USER_SCALE}",
      "Subscription model: {PRICING_MODEL}"
    ],
    "steps": [
      "Design scalable system architecture with microservices approach",
      "Create complete codebase with proper file structure and best practices",
      "Implement secure authentication system with JWT and OAuth",
      "Integrate Stripe payment processing with subscription management",
      "Set up CI/CD pipeline and deployment configuration",
      "Add comprehensive monitoring, logging, and analytics",
      "Create user onboarding flow and admin dashboard",
      "Generate API documentation and user guides"
    ],
    "constraints": [
      "Production-ready code only - no placeholder functions",
      "Include comprehensive security measures (OWASP guidelines)",
      "Mobile-responsive design with 95%+ lighthouse scores",
      "Database queries optimized for 10,000+ concurrent users",
      "Include automated testing suite with 80%+ coverage",
      "All dependencies properly managed and documented"
    ],
    "output": "Complete deployable application package including: (1) Full codebase, (2) Database schemas with migrations, (3) Deployment scripts, (4) Environment configuration, (5) API documentation, (6) User documentation, (7) Marketing landing page, (8) Pricing page template",
    "review": [
      "✓ Code follows industry best practices and is security-audited",
      "✓ Application can handle expected user load",
      "✓ Payment integration is properly tested",
      "✓ Deployment process is documented and automated",
      "✓ User experience is intuitive and conversion-optimized"
    ]
  }
}
```

### 2. AI-Powered Mobile App Generator
**ID**: `mobile_app_ai`
**Category**: software_development
**Priority**: 1

```json
{
  "id": "mobile_app_ai",
  "name": "AI-Powered Mobile App Generator",
  "category": "software_development",
  "surfaces": ["chatgpt", "claude", "generic"],
  "useCase": "mobile_development",
  "priority": 1,
  "variables": {
    "INDUSTRY": "healthcare, fitness, education, etc.",
    "AI_FEATURE": "recommendation, analysis, prediction, etc.",
    "PLATFORM": "iOS, Android, or both",
    "MONETIZATION": "freemium, subscription, ads, etc."
  },
  "template": {
    "role": "Act as a senior mobile app developer and AI integration specialist with expertise in React Native and native AI frameworks.",
    "context": "Create a complete AI-powered mobile application for {INDUSTRY} that leverages {AI_FEATURE} to provide significant user value.",
    "inputs": [
      "Target industry: {INDUSTRY}",
      "AI functionality: {AI_FEATURE}",
      "Platform preference: {PLATFORM}",
      "Monetization strategy: {MONETIZATION}",
      "Target audience: {AUDIENCE}",
      "Competitive advantage: {UNIQUE_VALUE}"
    ],
    "steps": [
      "Design user-centric app architecture with AI at the core",
      "Create complete React Native/Flutter codebase with native modules",
      "Integrate AI/ML models (TensorFlow, Core ML, or cloud APIs)",
      "Implement secure user authentication and data handling",
      "Add in-app purchases and subscription management",
      "Create engaging onboarding and user retention features",
      "Set up push notifications and offline capabilities",
      "Generate app store assets and submission materials"
    ],
    "constraints": [
      "Follow platform-specific design guidelines (iOS HIG, Material Design)",
      "Optimize for performance on mid-range devices",
      "Include comprehensive error handling and edge cases",
      "Implement proper data privacy and GDPR compliance",
      "Design for offline-first architecture where possible",
      "Include analytics and user behavior tracking"
    ],
    "output": "Complete mobile app package including: (1) Full source code, (2) AI model integration, (3) Backend API if needed, (4) App store assets, (5) Marketing materials, (6) User acquisition strategy, (7) Monetization implementation",
    "review": [
      "✓ AI features provide clear user value and work reliably",
      "✓ App performance meets platform standards",
      "✓ Monetization strategy is properly implemented",
      "✓ User experience is intuitive and engaging",
      "✓ App store submission requirements are met"
    ]
  }
}
```

### 3. API Development & Documentation
**ID**: `api_development_complete`
**Category**: software_development
**Priority**: 2

```json
{
  "id": "api_development_complete",
  "name": "Complete API Development & Documentation",
  "category": "software_development",
  "surfaces": ["chatgpt", "claude", "generic"],
  "useCase": "backend_development",
  "priority": 2,
  "variables": {
    "API_TYPE": "REST, GraphQL, or gRPC",
    "DATA_SOURCE": "database, external APIs, files, etc.",
    "FRAMEWORK": "Express, FastAPI, Django, etc.",
    "AUTHENTICATION": "JWT, OAuth, API keys, etc."
  },
  "template": {
    "role": "Act as a senior backend developer and API architect with expertise in scalable API design and documentation.",
    "context": "Create a complete, production-ready {API_TYPE} API that connects to {DATA_SOURCE} with comprehensive documentation and security measures.",
    "inputs": [
      "API type: {API_TYPE}",
      "Data source: {DATA_SOURCE}",
      "Preferred framework: {FRAMEWORK}",
      "Authentication method: {AUTHENTICATION}",
      "Expected traffic: {TRAFFIC_VOLUME}",
      "Key endpoints needed: {ENDPOINTS}"
    ],
    "steps": [
      "Design RESTful/GraphQL API architecture with clear resource modeling",
      "Implement complete API endpoints with proper HTTP methods and status codes",
      "Add comprehensive input validation and error handling",
      "Integrate secure authentication and authorization system",
      "Implement rate limiting, caching, and performance optimization",
      "Create extensive API documentation with examples",
      "Add comprehensive testing suite (unit, integration, load tests)",
      "Set up monitoring, logging, and health checks"
    ],
    "constraints": [
      "Follow API design best practices and RESTful principles",
      "Include comprehensive security measures (OWASP API Security)",
      "Optimize for high performance and scalability",
      "Provide clear, interactive documentation (Swagger/Postman)",
      "Include proper versioning strategy",
      "Design for backward compatibility"
    ],
    "output": "Complete API package including: (1) Full API implementation, (2) Interactive documentation, (3) Authentication system, (4) Testing suite, (5) Deployment configuration, (6) Performance monitoring setup, (7) Client SDK examples",
    "review": [
      "✓ API follows industry standards and best practices",
      "✓ Security measures are comprehensive and tested",
      "✓ Documentation is clear and includes working examples",
      "✓ Performance meets scalability requirements",
      "✓ Error handling covers all edge cases"
    ]
  }
}
```

---

## BUSINESS & MARKETING TEMPLATES (20)

### 1. Complete Business Plan Generator
**ID**: `business_plan_complete`
**Category**: business_marketing
**Priority**: 1

```json
{
  "id": "business_plan_complete",
  "name": "Complete Business Plan Generator",
  "category": "business_marketing",
  "surfaces": ["chatgpt", "claude", "generic"],
  "useCase": "business_strategy",
  "priority": 1,
  "variables": {
    "BUSINESS_IDEA": "core concept description",
    "TARGET_MARKET": "primary audience",
    "FUNDING_NEEDED": "investment requirements",
    "TIMELINE": "launch timeline"
  },
  "template": {
    "role": "Act as a seasoned business consultant and venture capital advisor with 15+ years of experience in successful business planning.",
    "context": "Create a comprehensive, investor-ready business plan for {BUSINESS_IDEA} targeting {TARGET_MARKET} with clear monetization strategy and growth projections.",
    "inputs": [
      "Business concept: {BUSINESS_IDEA}",
      "Target market: {TARGET_MARKET}",
      "Funding requirements: {FUNDING_NEEDED}",
      "Launch timeline: {TIMELINE}",
      "Competitive landscape: {COMPETITORS}",
      "Founder background: {FOUNDER_EXPERIENCE}"
    ],
    "steps": [
      "Conduct thorough market analysis and opportunity assessment",
      "Develop clear value proposition and competitive advantages",
      "Create detailed financial projections for 3-5 years",
      "Design comprehensive go-to-market strategy",
      "Outline operational plan and organizational structure",
      "Identify key risks and mitigation strategies",
      "Develop funding strategy and investor pitch materials",
      "Create implementation timeline with key milestones"
    ],
    "constraints": [
      "Use realistic market data and financial projections",
      "Include contingency plans for different scenarios",
      "Format for professional presentation to investors",
      "Ensure all claims are supported by data or research",
      "Include clear success metrics and KPIs",
      "Design for scalability and growth"
    ],
    "output": "Complete business plan package including: (1) Executive summary, (2) Market analysis, (3) Financial projections, (4) Marketing strategy, (5) Operational plan, (6) Risk assessment, (7) Funding requirements, (8) Investor pitch deck",
    "review": [
      "✓ Market opportunity is clearly quantified and validated",
      "✓ Financial projections are realistic and well-supported",
      "✓ Go-to-market strategy is detailed and executable",
      "✓ Risk assessment covers major potential challenges",
      "✓ Funding requirements align with business objectives"
    ]
  }
}
```

### 2. Viral Marketing Campaign Creator
**ID**: `viral_marketing_campaign`
**Category**: business_marketing
**Priority**: 1

```json
{
  "id": "viral_marketing_campaign",
  "name": "Viral Marketing Campaign Creator",
  "category": "business_marketing",
  "surfaces": ["chatgpt", "claude", "generic"],
  "useCase": "marketing_strategy",
  "priority": 1,
  "variables": {
    "PRODUCT": "product or service to promote",
    "AUDIENCE": "target demographic",
    "BUDGET": "marketing budget available",
    "TIMELINE": "campaign duration"
  },
  "template": {
    "role": "Act as a viral marketing expert and social media strategist who has created multiple campaigns with 1M+ engagements.",
    "context": "Design a comprehensive viral marketing campaign for {PRODUCT} that maximizes reach and engagement within {TIMELINE} and {BUDGET} constraints.",
    "inputs": [
      "Product/service: {PRODUCT}",
      "Target audience: {AUDIENCE}",
      "Campaign budget: {BUDGET}",
      "Timeline: {TIMELINE}",
      "Key message: {CORE_MESSAGE}",
      "Available channels: {CHANNELS}"
    ],
    "steps": [
      "Identify viral potential and unique angles for maximum shareability",
      "Create multi-platform content strategy with platform-specific adaptations",
      "Design influencer outreach and partnership strategy",
      "Develop user-generated content campaigns and hashtag strategies",
      "Create compelling visual assets and video content concepts",
      "Plan strategic timing and momentum-building tactics",
      "Set up tracking and analytics for real-time optimization",
      "Prepare crisis management and negative feedback response protocols"
    ],
    "constraints": [
      "Focus on authentic engagement over vanity metrics",
      "Ensure compliance with platform advertising policies",
      "Design for mobile-first consumption patterns",
      "Include clear call-to-action and conversion tracking",
      "Plan for scalability if campaign goes viral",
      "Maintain brand consistency across all touchpoints"
    ],
    "output": "Complete campaign package including: (1) Creative concepts and assets, (2) Content calendar, (3) Influencer outreach templates, (4) Hashtag strategy, (5) Paid promotion plan, (6) Analytics dashboard, (7) Crisis management plan, (8) Success metrics and KPIs",
    "review": [
      "✓ Campaign concepts have clear viral potential and shareability",
      "✓ Content is tailored to each platform's audience and format",
      "✓ Budget allocation maximizes reach and engagement",
      "✓ Success metrics align with business objectives",
      "✓ Campaign can be executed within timeline constraints"
    ]
  }
}
```

---

## CREATIVE & CONTENT TEMPLATES (15)

### 1. Comprehensive Course Creation System
**ID**: `course_creation_complete`
**Category**: creative_content
**Priority**: 1

```json
{
  "id": "course_creation_complete",
  "name": "Comprehensive Online Course Creation System",
  "category": "creative_content",
  "surfaces": ["chatgpt", "claude", "generic"],
  "useCase": "education_content",
  "priority": 1,
  "variables": {
    "TOPIC": "course subject matter",
    "SKILL_LEVEL": "beginner, intermediate, advanced",
    "DURATION": "course length in hours/weeks",
    "PLATFORM": "Udemy, Teachable, etc."
  },
  "template": {
    "role": "Act as an instructional designer and online education expert with experience creating courses that have generated $100K+ in revenue.",
    "context": "Create a complete online course on {TOPIC} for {SKILL_LEVEL} learners that delivers measurable skill improvement in {DURATION}.",
    "inputs": [
      "Course topic: {TOPIC}",
      "Target skill level: {SKILL_LEVEL}",
      "Course duration: {DURATION}",
      "Delivery platform: {PLATFORM}",
      "Learning objectives: {OBJECTIVES}",
      "Target price point: {PRICE_RANGE}"
    ],
    "steps": [
      "Conduct comprehensive learning needs analysis and skill gap assessment",
      "Design modular curriculum with clear learning progression",
      "Create detailed lesson plans with engaging activities and assessments",
      "Develop multimedia content including videos, worksheets, and interactive elements",
      "Build practical projects and real-world applications",
      "Create comprehensive student resources and reference materials",
      "Design effective marketing and sales funnel for course promotion",
      "Set up student community and ongoing support systems"
    ],
    "constraints": [
      "Ensure each module has clear learning outcomes and assessments",
      "Include practical, hands-on projects students can add to portfolios",
      "Design for various learning styles (visual, auditory, kinesthetic)",
      "Optimize content for chosen platform's best practices",
      "Include strategies for student engagement and completion rates",
      "Provide ongoing value that justifies premium pricing"
    ],
    "output": "Complete course package including: (1) Detailed curriculum outline, (2) Lesson scripts and materials, (3) Video production guidelines, (4) Student worksheets and resources, (5) Assessment rubrics, (6) Marketing materials, (7) Sales page copy, (8) Student onboarding sequence",
    "review": [
      "✓ Learning objectives are specific, measurable, and achievable",
      "✓ Course content provides clear value progression",
      "✓ Projects and assessments reinforce key concepts",
      "✓ Marketing strategy targets the right audience effectively",
      "✓ Pricing strategy reflects value delivered and market positioning"
    ]
  }
}
```

---

## PRODUCTIVITY & AUTOMATION TEMPLATES (15)

### 1. Complete Workflow Automation System
**ID**: `workflow_automation_complete`
**Category**: productivity_automation
**Priority**: 1

```json
{
  "id": "workflow_automation_complete",
  "name": "Complete Workflow Automation System",
  "category": "productivity_automation",
  "surfaces": ["chatgpt", "claude", "generic"],
  "useCase": "process_automation",
  "priority": 1,
  "variables": {
    "PROCESS_TYPE": "sales, marketing, operations, etc.",
    "TOOLS_AVAILABLE": "Zapier, Make, custom scripts, etc.",
    "TEAM_SIZE": "number of users",
    "COMPLEXITY": "simple, moderate, complex"
  },
  "template": {
    "role": "Act as a business process automation expert and workflow optimization consultant with expertise in no-code/low-code solutions.",
    "context": "Design and implement a complete workflow automation system for {PROCESS_TYPE} that reduces manual work by 80%+ and improves accuracy for a team of {TEAM_SIZE}.",
    "inputs": [
      "Process to automate: {PROCESS_TYPE}",
      "Available automation tools: {TOOLS_AVAILABLE}",
      "Team size: {TEAM_SIZE}",
      "Process complexity: {COMPLEXITY}",
      "Current pain points: {PAIN_POINTS}",
      "Success metrics: {SUCCESS_METRICS}"
    ],
    "steps": [
      "Map current workflow and identify automation opportunities",
      "Design optimized process flow with decision points and exceptions",
      "Select appropriate automation tools and integration methods",
      "Create automated workflows with error handling and notifications",
      "Set up data validation and quality control measures",
      "Implement monitoring and reporting dashboards",
      "Create training materials and change management plan",
      "Establish maintenance and optimization procedures"
    ],
    "constraints": [
      "Ensure automation handles edge cases and error scenarios",
      "Design for scalability as team and processes grow",
      "Include human oversight and approval points where necessary",
      "Maintain audit trails and compliance requirements",
      "Optimize for reliability and uptime (99%+ availability)",
      "Keep total cost of ownership within budget constraints"
    ],
    "output": "Complete automation package including: (1) Process flow diagrams, (2) Automation configurations, (3) Integration setup guides, (4) Error handling procedures, (5) Monitoring dashboard, (6) Training materials, (7) Maintenance schedule, (8) ROI analysis and metrics",
    "review": [
      "✓ Automation reduces manual work by target percentage",
      "✓ Error handling covers all identified edge cases",
      "✓ Team can easily maintain and modify automations",
      "✓ ROI projections are realistic and measurable",
      "✓ System integrates seamlessly with existing tools"
    ]
  }
}
```

---

## SPECIALIZED INDUSTRY TEMPLATES (25)

### 1. Complete E-commerce Solution
**ID**: `ecommerce_solution_complete`
**Category**: specialized_industry
**Priority**: 1

```json
{
  "id": "ecommerce_solution_complete",
  "name": "Complete E-commerce Solution Builder",
  "category": "specialized_industry",
  "surfaces": ["chatgpt", "claude", "generic"],
  "useCase": "ecommerce_development",
  "priority": 1,
  "variables": {
    "PRODUCT_TYPE": "physical, digital, services, etc.",
    "PLATFORM": "Shopify, WooCommerce, custom, etc.",
    "MARKET": "B2B, B2C, marketplace, etc.",
    "SCALE": "startup, SME, enterprise"
  },
  "template": {
    "role": "Act as an e-commerce solution architect and digital marketing expert with experience building stores that generate $1M+ annual revenue.",
    "context": "Create a complete e-commerce solution for {PRODUCT_TYPE} targeting {MARKET} customers with projected {SCALE} requirements and full conversion optimization.",
    "inputs": [
      "Product type: {PRODUCT_TYPE}",
      "Preferred platform: {PLATFORM}",
      "Target market: {MARKET}",
      "Business scale: {SCALE}",
      "Key features needed: {FEATURES}",
      "Integration requirements: {INTEGRATIONS}"
    ],
    "steps": [
      "Design conversion-optimized store architecture and user experience",
      "Implement complete product catalog with rich media and descriptions",
      "Set up secure payment processing and multiple payment options",
      "Create comprehensive inventory management and order fulfillment system",
      "Implement advanced SEO and conversion rate optimization",
      "Set up email marketing automation and customer retention programs",
      "Create comprehensive analytics and reporting dashboard",
      "Establish customer service and support systems"
    ],
    "constraints": [
      "Optimize for mobile-first shopping experience",
      "Ensure PCI compliance and data security standards",
      "Design for international sales and multi-currency support",
      "Include comprehensive fraud protection measures",
      "Optimize page load speeds for better conversion rates",
      "Ensure scalability for traffic and sales volume growth"
    ],
    "output": "Complete e-commerce package including: (1) Fully configured store, (2) Product catalog setup, (3) Payment and shipping configuration, (4) Marketing automation setup, (5) Analytics dashboard, (6) SEO optimization, (7) Customer service tools, (8) Growth and scaling strategy",
    "review": [
      "✓ Store is optimized for conversion and user experience",
      "✓ All payment and security measures are properly implemented",
      "✓ Marketing automation drives customer acquisition and retention",
      "✓ Analytics provide actionable insights for optimization",
      "✓ Solution can scale with business growth requirements"
    ]
  }
}
```

---

## Template Usage Guidelines

### Integration with Chrome Extension

1. **Template Selection**: Based on intent detection algorithm
2. **Variable Extraction**: Automatic parsing from user input
3. **Template Composition**: Dynamic variable replacement
4. **Output Optimization**: Format for target AI platform

### Customization Options

- **Style Variants**: Formal, Casual, Technical
- **Length Options**: Concise, Standard, Detailed
- **Complexity Levels**: Basic, Intermediate, Expert

### Performance Metrics

- **Template Effectiveness**: User acceptance rate
- **Value Generation**: Output quality ratings
- **Usage Patterns**: Most popular templates by category
- **Improvement Opportunities**: Low-performing template identification

---

This template library provides the foundation for the Prompter Chrome extension, ensuring users can transform simple ideas into comprehensive, professional prompts that deliver exceptional AI results.
