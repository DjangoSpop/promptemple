# PromptCraft Unified System Documentation

## Overview

The PromptCraft Flutter app has been completely modernized with a unified API architecture that consolidates all authentication, user management, template CRUD operations, gamification, and analytics into a cohesive, maintainable system.

## Architecture

### Core Components

1. **Unified API Models** (`lib/data/models/unified_api_models.dart`)
   - All data models matching the backend OpenAPI specification
   - User, Template, Category, Field, and response models
   - Type-safe field definitions and validation

2. **Unified API Service** (`lib/data/services/unified_api_service.dart`)
   - Single service handling all API communications
   - Reactive state management with GetX
   - Automatic token management and refresh
   - Comprehensive error handling

3. **Specialized Controllers**
   - `UnifiedAuthController` - Authentication and user management
   - `TemplateController` - Template CRUD and operations
   - `GamificationController` - Achievements, challenges, leaderboards
   - `AnalyticsController` - Dashboard and user insights

4. **Configuration** (`lib/core/config/api_config.dart`)
   - Environment-aware API endpoint management
   - Easy switching between development and production

## Quick Start

### 1. Basic Setup

The unified system is automatically initialized when the app starts via `initial_bindings.dart`. All services and controllers are registered and ready to use.

```dart
// Access controllers anywhere in your app
final auth = Get.find<UnifiedAuthController>();
final templates = Get.find<TemplateController>();
final gamification = Get.find<GamificationController>();
final analytics = Get.find<AnalyticsController>();

// Or use the convenient extensions
final user = Get.auth.currentUser;
final myTemplates = Get.templates.myTemplates;
```

### 2. Authentication Flow

```dart
// Register a new user
final success = await Get.auth.register(
  username: 'john_doe',
  email: 'john@example.com',
  password: 'securepassword123',
  passwordConfirm: 'securepassword123',
  firstName: 'John',
  lastName: 'Doe',
);

// Login
await Get.auth.login(
  username: 'john_doe',
  password: 'securepassword123',
);

// Check authentication status
if (Get.auth.isAuthenticated) {
  print('Welcome ${Get.auth.fullName}!');
}

// Update profile
await Get.auth.updateProfile(
  firstName: 'Johnny',
  bio: 'AI enthusiast',
  themePreference: 'dark',
);

// Logout
await Get.auth.logout();
```

### 3. Template Management

```dart
// Load templates with filters
await Get.templates.loadTemplates(refresh: true);

// Search templates
Get.templates.updateSearch('blog writing');
Get.templates.updateCategoryFilter(1); // Writing category

// Create a new template
final fields = [
  FieldData(
    label: 'Topic',
    fieldType: FieldType.text,
    isRequired: true,
    order: 1,
  ),
  FieldData(
    label: 'Tone',
    fieldType: FieldType.dropdown,
    isRequired: true,
    options: ['Professional', 'Casual', 'Creative'],
    order: 2,
  ),
];

await Get.templates.createTemplate(
  title: 'Blog Post Generator',
  description: 'Generate engaging blog posts',
  categoryId: 1,
  content: 'Write a {{tone}} blog post about {{topic}}...',
  isPublic: true,
  fields: fields,
);

// Use a template
await Get.templates.startTemplateUsage(templateId);
await Get.templates.completeTemplateUsage(templateId);
await Get.templates.rateTemplate(templateId, 5, review: 'Great template!');
```

### 4. Gamification

```dart
// Load user achievements
await Get.gamification.loadAchievements();
print('Completed: ${Get.gamification.completedAchievementsCount}');

// Load daily challenges
await Get.gamification.loadDailyChallenges();

// Check leaderboard
await Get.gamification.loadLeaderboard();
final position = Get.gamification.userLeaderboardPosition;
final topUsers = Get.gamification.getTopUsers(10);

// Complete a challenge
await Get.gamification.completeDailyChallenge(challengeId);
```

### 5. Analytics

```dart
// Load analytics dashboard
await Get.analytics.loadDashboardAnalytics();
print('Total Templates: ${Get.analytics.totalTemplatesCreated}');
print('Engagement Rate: ${Get.analytics.engagementRate}');

// Load user insights
await Get.analytics.loadUserInsights();
print('Most Used Category: ${Get.analytics.mostUsedCategory}');
print('Productivity Score: ${Get.analytics.productivityScore}');

// Load template analytics
await Get.analytics.loadTemplateAnalytics();
final topTemplates = Get.analytics.topTemplates;
```

## State Management

The unified system uses GetX for reactive state management:

```dart
// Observe authentication state
Obx(() {
  if (Get.auth.isLoading.value) {
    return CircularProgressIndicator();
  }
  if (Get.auth.currentUser.value != null) {
    return UserDashboard();
  }
  return LoginScreen();
});

// Observe template list
Obx(() {
  final templates = Get.templates.filteredTemplates;
  return ListView.builder(
    itemCount: templates.length,
    itemBuilder: (context, index) => TemplateCard(templates[index]),
  );
});

// Listen to errors
Get.auth.errorMessage.listen((error) {
  if (error.isNotEmpty) {
    Get.snackbar('Error', error);
  }
});
```

## Error Handling

The unified system provides comprehensive error handling:

```dart
try {
  await Get.auth.login(username: 'user', password: 'pass');
} catch (e) {
  if (e is ApiException) {
    print('API Error: ${e.message} (${e.statusCode})');
    if (e.details != null) {
      print('Details: ${e.details}');
    }
  }
}

// Check field-specific errors
if (Get.auth.fieldErrors.value != null) {
  Get.auth.fieldErrors.value!.forEach((field, error) {
    print('$field: $error');
  });
}
```

## Configuration

### Environment Setup

```dart
// lib/core/config/api_config.dart
class ApiConfig {
  static const String environment = 'development'; // or 'production'
  
  static String get baseUrl {
    switch (environment) {
      case 'production':
        return 'https://api.promptcraft.com';
      case 'staging':
        return 'https://staging-api.promptcraft.com';
      default:
        return 'http://localhost:8000';
    }
  }
}
```

### Custom Headers

```dart
// The unified service automatically handles:
// - Authorization headers
// - Content-Type headers
// - API versioning
// - User-Agent identification
```

## Migration Guide

### From Legacy Services

The new unified system coexists with legacy services during migration:

```dart
// Old way (still works)
final legacyAuth = Get.find<AuthController>();
final legacyApi = Get.find<ApiService>();

// New way (recommended)
final unifiedAuth = Get.find<UnifiedAuthController>();
final unifiedApi = Get.find<UnifiedApiService>();
```

### Recommended Migration Steps

1. **Update your widgets** to use the new controllers
2. **Test all functionality** with the new system
3. **Remove legacy service dependencies** once verified
4. **Update imports** to use unified models
5. **Clean up unused legacy files**

## Features

### Authentication
- ✅ User registration with validation
- ✅ Secure login/logout
- ✅ Automatic token refresh
- ✅ Profile management
- ✅ Password changes
- ✅ Session persistence

### Templates
- ✅ CRUD operations
- ✅ Advanced filtering and search
- ✅ Category management
- ✅ Field definitions
- ✅ Usage tracking
- ✅ Rating system
- ✅ Featured/trending templates

### Gamification
- ✅ Achievement system
- ✅ Daily challenges
- ✅ Leaderboards
- ✅ Experience points
- ✅ User levels and ranks
- ✅ Badge collections

### Analytics
- ✅ Dashboard metrics
- ✅ User insights
- ✅ Template performance
- ✅ Usage trends
- ✅ Engagement tracking

### Technical
- ✅ Reactive state management
- ✅ Type-safe models
- ✅ Comprehensive error handling
- ✅ Automatic retries
- ✅ Offline support
- ✅ Environment configuration

## API Endpoints

All endpoints are defined in `ApiConfig` and automatically used by the `UnifiedApiService`:

```dart
// Authentication
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/

// User Management
GET /api/users/profile/
PATCH /api/users/profile/
POST /api/users/change-password/

// Templates
GET /api/templates/
POST /api/templates/
GET /api/templates/{id}/
PUT /api/templates/{id}/
DELETE /api/templates/{id}/
POST /api/templates/{id}/use/
POST /api/templates/{id}/complete/
POST /api/templates/{id}/rate/

// Gamification
GET /api/gamification/achievements/
GET /api/gamification/daily-challenges/
GET /api/gamification/leaderboard/
POST /api/gamification/daily-challenges/{id}/complete/

// Analytics
GET /api/analytics/dashboard/
GET /api/analytics/user-insights/
GET /api/analytics/templates/
```

## Testing

For comprehensive testing examples, see:
- `lib/examples/unified_system_usage.dart` - Complete usage examples
- Test files demonstrate all major workflows

## Support

The unified system is designed to be:
- **Maintainable** - Single source of truth for API logic
- **Scalable** - Easy to extend with new features
- **Reliable** - Comprehensive error handling and retries
- **Developer-friendly** - Clear APIs and extensive documentation

For additional help or questions about the unified system, refer to the example usage file or contact the development team.
