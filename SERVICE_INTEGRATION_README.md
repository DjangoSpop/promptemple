# PromptCraft Flutter Integration Documentation

## 🚀 Complete Service Layer Integration with Django Backend

This document outlines the complete integration between the Flutter frontend and Django REST Framework backend using the provided OpenAPI YAML specification.

### 📁 Project Structure

```
lib/
├── bindings/
│   └── initial_binding.dart              # Dependency injection setup
├── controllers/
│   ├── auth_controller_new.dart          # Authentication controller
│   ├── template_controller_new.dart      # Template management controller
│   └── gamification_controller.dart     # Gamification features controller
├── models/
│   └── api_models_new.dart               # All API models matching OpenAPI spec
├── services/
│   ├── api_client_new.dart               # Main API client with all endpoints
│   └── auth_service.dart                 # Enhanced authentication service
└── main_with_new_services.dart           # Sample app using new services
```

## 🔧 Features Implemented

### ✅ Authentication System
- JWT token management with automatic refresh
- Secure token storage using Flutter Secure Storage
- Login, register, logout functionality
- Profile management
- Password change functionality

### ✅ Template Management
- CRUD operations for templates
- Pagination support
- Search and filtering
- Category management
- Template usage tracking
- Rating and review system
- Template duplication
- AI-powered template analysis

### ✅ Gamification System
- Achievement tracking
- Daily challenges
- User level and XP system
- Leaderboard functionality
- Streak management
- Badge system

### ✅ AI Integration
- Template analysis with AI
- Content enhancement
- AI quota management
- Recommendation system

### ✅ Error Handling & Offline Support
- Comprehensive error handling with custom APIException
- Automatic token refresh on 401 errors
- Network connectivity checking
- Local caching for offline support
- Retry mechanism for failed requests

## 🛠️ Setup Instructions

### 1. Install Dependencies

Add to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  get: ^4.6.6
  get_storage: ^2.1.1
  dio: ^5.8.0+1
  flutter_secure_storage: ^9.0.0
  jwt_decoder: ^3.1.0
  connectivity_plus: ^5.0.2
  device_info_plus: ^11.3.0
  package_info_plus: ^8.3.0
```

Run:
```bash
flutter pub get
```

### 2. Initialize Services

In your `main.dart`:

```dart
import 'package:get_storage/get_storage.dart';
import 'bindings/initial_binding.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await GetStorage.init();
  
  runApp(GetMaterialApp(
    initialBinding: InitialBinding(),
    home: AuthWrapper(),
  ));
}
```

### 3. Configure API Base URL

Update the base URL in `api_client_new.dart`:

```dart
static const String baseUrl = 'http://your-django-server.com/api/v1';
```

## 📚 Usage Examples

### Authentication

```dart
// Get the auth controller
final authController = Get.find<AuthController>();

// Login
await authController.login();

// Register
await authController.register();

// Update profile
await authController.updateProfile(
  newFirstName: 'John',
  newLastName: 'Doe',
  themePreference: ThemePreference.dark,
);

// Change password
await authController.changePassword('oldPassword', 'newPassword');

// Logout
await authController.logout();
```

### Template Management

```dart
// Get the template controller
final templateController = Get.find<TemplateController>();

// Load templates with filters
await templateController.loadTemplates();

// Search templates
templateController.searchQuery.value = 'AI prompt';

// Filter by category
templateController.setCategory(selectedCategory);

// Create a new template
final request = TemplateCreateRequest(
  title: 'My AI Prompt',
  description: 'A great prompt for AI',
  templateContent: 'Generate a {{type}} about {{topic}}',
  category: 1,
  tags: ['AI', 'creative'],
);
await templateController.createTemplate(request);

// Use a template
final usage = await templateController.startTemplateUsage(templateId);
// ... use the template ...
await templateController.completeTemplateUsage(
  templateId,
  usageId: usage!.usageId,
  timeSpentSeconds: 120,
  promptLength: 150,
);

// Rate a template
await templateController.rateTemplate(templateId, 5, review: 'Excellent!');
```

### Gamification

```dart
// Get the gamification controller
final gamificationController = Get.find<GamificationController>();

// Load achievements
await gamificationController.loadAchievements();

// Get daily challenges
final activeChallenges = gamificationController.activeDailyChallenges;

// Check user level progress
final progressToNext = gamificationController.progressToNextLevel;

// Get current streak
final streakDays = gamificationController.currentStreakDays;
```

### Direct API Client Usage

```dart
final apiClient = PromptCraftAPI();

// Get health status
final health = await apiClient.getHealthStatus();

// Get app configuration
final config = await apiClient.getAppConfig();

// Track custom events
await apiClient.trackEvent(
  'custom_event',
  category: 'user_interaction',
  properties: {'action': 'button_click'},
);
```

## 🔒 Security Features

- **Secure Token Storage**: Uses Flutter Secure Storage with encryption
- **Automatic Token Refresh**: Handles token expiration transparently
- **Request Interceptors**: Automatically adds auth headers
- **Error Recovery**: Retries failed requests after token refresh

## 📊 Analytics & Tracking

The system includes comprehensive analytics tracking:

- User authentication events
- Template usage patterns
- Gamification interactions
- Error occurrences
- Performance metrics

## 🧪 Testing

Run the API integration tests:

```bash
flutter test test/api_integration_test.dart
```

The tests cover:
- Model serialization/deserialization
- API endpoint functionality
- Error handling scenarios
- Authentication flows

## 📋 API Endpoints Covered

### Authentication (`/auth/`)
- ✅ POST `/login/` - User login
- ✅ POST `/register/` - User registration
- ✅ POST `/logout/` - User logout
- ✅ POST `/refresh/` - Token refresh
- ✅ GET `/profile/` - Get user profile
- ✅ PATCH `/profile/` - Update profile
- ✅ POST `/change-password/` - Change password
- ✅ GET `/stats/` - Get user stats

### Templates (`/templates/`)
- ✅ GET `/` - List templates with pagination/filtering
- ✅ POST `/` - Create template
- ✅ GET `/{id}/` - Get single template
- ✅ PUT `/{id}/` - Update template
- ✅ DELETE `/{id}/` - Delete template
- ✅ GET `/featured/` - Get featured templates
- ✅ GET `/trending/` - Get trending templates
- ✅ GET `/my_templates/` - Get user's templates
- ✅ GET `/search_suggestions/` - Get search suggestions
- ✅ POST `/{id}/start_usage/` - Start template usage
- ✅ POST `/{id}/complete_usage/` - Complete usage
- ✅ POST `/{id}/rate_template/` - Rate template
- ✅ POST `/{id}/duplicate/` - Duplicate template
- ✅ GET `/{id}/analytics/` - Get template analytics
- ✅ POST `/{id}/analyze_with_ai/` - AI analysis

### Categories (`/templates/categories/`)
- ✅ GET `/` - List categories
- ✅ GET `/{id}/` - Get single category
- ✅ GET `/{id}/templates/` - Get category templates

### Gamification (`/gamification/`)
- ✅ GET `/achievements/` - Get achievements
- ✅ GET `/badges/` - Get user badges
- ✅ GET `/leaderboard/` - Get leaderboard
- ✅ GET `/daily-challenges/` - Get daily challenges
- ✅ GET `/user-level/` - Get user level info
- ✅ GET `/streak/` - Get streak info

### AI Services (`/ai/`)
- ✅ GET `/providers/` - Get AI providers
- ✅ GET `/models/` - Get AI models
- ✅ POST `/generate/` - Generate content
- ✅ GET `/usage/` - Get AI usage
- ✅ GET `/quotas/` - Get AI quotas

### Analytics (`/analytics/`)
- ✅ GET `/dashboard/` - Dashboard analytics
- ✅ GET `/user-insights/` - User insights
- ✅ GET `/template-analytics/` - Template analytics
- ✅ GET `/recommendations/` - Get recommendations

### Core (`/core/`)
- ✅ GET `/health/` - Health check
- ✅ GET `/config/` - App configuration
- ✅ GET `/notifications/` - Get notifications
- ✅ POST `/notifications/` - Mark notification as read

## 🚨 Error Handling

The system provides comprehensive error handling:

```dart
try {
  final templates = await templateController.loadTemplates();
} catch (e) {
  if (e is APIException) {
    // Handle specific API errors
    print('API Error: ${e.message} (Status: ${e.statusCode})');
  } else {
    // Handle other errors
    print('Unexpected error: $e');
  }
}
```

## 🔄 State Management

Uses GetX for reactive state management:

```dart
// Reactive UI updates
Obx(() => templateController.isLoading.value
  ? CircularProgressIndicator()
  : ListView.builder(...));

// Listen to auth state changes
ever(authService.isAuthenticated, (authenticated) {
  if (!authenticated) {
    Get.offAllNamed('/login');
  }
});
```

## 🎯 Best Practices

1. **Always handle errors**: Use try-catch blocks around API calls
2. **Use reactive UI**: Leverage Obx widgets for automatic updates
3. **Cache data**: Use the built-in caching for offline support
4. **Track analytics**: Use the tracking methods for user insights
5. **Validate input**: Always validate user input before API calls
6. **Handle loading states**: Show loading indicators during API calls

## 🔧 Customization

### Adding New Endpoints

1. Add the method to `PromptCraftAPI` class
2. Create corresponding models if needed
3. Add controller methods if using GetX
4. Write tests for the new functionality

### Extending Models

1. Add new fields to the model classes
2. Update `fromJson` and `toJson` methods
3. Update any related API calls
4. Test serialization/deserialization

## 🚀 Deployment

For production deployment:

1. Update API base URLs to production endpoints
2. Configure proper error tracking (e.g., Sentry)
3. Enable/disable debug logging based on build mode
4. Set up proper SSL certificate pinning
5. Configure obfuscation for sensitive code

---

This integration provides a complete, production-ready service layer that matches your Django backend API specification. All endpoints are implemented with proper error handling, caching, and state management using Flutter best practices.
