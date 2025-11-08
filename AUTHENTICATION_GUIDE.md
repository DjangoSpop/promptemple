# Authentication Management Guide

**Created:** October 28, 2025  
**Purpose:** Simple JWT authentication for AI Services Testing Dashboard

## 🎯 Overview

A professional web-based authentication interface for managing JWT tokens used by PromptCraft AI services. Provides sign-in, sign-up, and automatic token storage in localStorage.

## 🚀 Quick Start

### Access Authentication Page
```
http://127.0.0.1:8000/auth/
```

### Features

✅ **Sign Up** - Create new account with username, email, and password  
✅ **Sign In** - Login with email or username  
✅ **Auto Token Storage** - JWT tokens automatically saved to localStorage  
✅ **User Dashboard** - Shows current user info, credits, and level  
✅ **Token Management** - Copy, view, and clear tokens easily  
✅ **Welcome Bonus** - New users automatically receive 50 credits  
✅ **Seamless Integration** - Works with all AI test pages  

## 📋 User Flow

### 1. New User Registration

```
Visit: http://127.0.0.1:8000/auth/
→ Click "Sign Up" tab
→ Enter username, email, password
→ Submit form
→ Receive JWT token + 50 welcome credits
→ Token stored in localStorage
→ Redirect to Dashboard
```

### 2. Existing User Login

```
Visit: http://127.0.0.1:8000/auth/
→ Click "Sign In" tab  
→ Enter email/username and password
→ Submit form
→ Receive JWT token
→ Token stored in localStorage
→ View daily streak bonus
→ Go to Dashboard
```

### 3. Using Protected Endpoints

```
Visit any AI test page (e.g., /ai-test/optimizer/)
→ JWT token automatically loaded from localStorage
→ Included in Authorization header
→ Test endpoint with authentication
```

## 🔧 Technical Details

### Backend Endpoints

#### Registration
```http
POST /api/users/register/
Content-Type: application/json

Request Body:
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepass123",
  "password2": "securepass123"
}

Response (201 Created):
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid-string",
    "username": "testuser",
    "email": "test@example.com",
    "credits": 150,
    "level": 1,
    "experience_points": 0,
    "daily_streak": 0,
    "user_rank": "Prompt Novice",
    "is_premium": false
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}

Error Response (400 Bad Request):
{
  "username": ["This username is already taken."],
  "email": ["User with this email already exists."],
  "password": ["This password is too common."]
}
```

#### Login
```http
POST /api/users/login/
Content-Type: application/json

Request Body:
{
  "email": "test@example.com",
  "password": "securepass123"
}

Response (200 OK):
{
  "message": "Login successful",
  "user": {
    "id": "uuid-string",
    "username": "testuser",
    "email": "test@example.com",
    "credits": 150,
    "level": 1,
    "daily_streak": 5
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "daily_streak": 5
}

Error Response (400 Bad Request):
{
  "message": "Login failed",
  "error": "Invalid credentials"
}
```

### Frontend Implementation

#### Token Storage
```javascript
// After successful login/registration
const { tokens, user } = responseData;

// Store tokens in localStorage
localStorage.setItem('access_token', tokens.access);
localStorage.setItem('refresh_token', tokens.refresh);
localStorage.setItem('user_data', JSON.stringify(user));
```

#### Using Tokens in API Calls
```javascript
// Get token from localStorage
const accessToken = localStorage.getItem('access_token');

// Make authenticated request
const response = await fetch('http://127.0.0.1:8000/api/ai/agent/optimize/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    session_id: 'unique-id',
    original: 'Write a blog post',
    mode: 'fast'
  })
});
```

#### Checking Authentication Status
```javascript
function isAuthenticated() {
  const accessToken = localStorage.getItem('access_token');
  const userData = localStorage.getItem('user_data');
  return !!(accessToken && userData);
}

function getCurrentUser() {
  const userData = localStorage.getItem('user_data');
  return userData ? JSON.parse(userData) : null;
}
```

#### Logout
```javascript
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_data');
  window.location.href = '/auth/';
}
```

## 🎨 UI Components

### Authentication Page (`/auth/`)

**Features:**
- Split-screen design with sidebar and form area
- Tab switching between Sign In and Sign Up
- Real-time validation with error messages
- Success messages with user info display
- Token display with copy functionality
- Automatic detection of existing authentication
- Logout button for authenticated users

**Form Validation:**
- Username: Min 3 characters
- Email: Valid email format
- Password: Min 8 characters
- Password confirmation must match

### Dashboard Integration (`/ai-test/`)

**JWT Status Bar:**
- Shows token status (Active/Not Set)
- Displays authenticated user info
- Copy JWT button for quick access
- Logout button
- Sign In/Sign Up button when not authenticated

## 🔒 Security Features

### Password Requirements
- Minimum 8 characters
- Django's built-in password validators
- Secure hashing with PBKDF2

### JWT Tokens
- Access token: Short-lived (configurable)
- Refresh token: Long-lived, can be blacklisted
- Token blacklist on logout
- Secure token generation with PyO3 fallback

### User Model Features
- UUID primary keys
- Email uniqueness validation
- Username uniqueness validation
- Automatic credit allocation
- Gamification tracking (XP, level, streak)

## 📊 User Data Structure

```javascript
// Stored in localStorage as 'user_data'
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "testuser",
  "email": "test@example.com",
  "credits": 150,
  "level": 1,
  "experience_points": 0,
  "daily_streak": 5,
  "user_rank": "Prompt Novice",
  "is_premium": false,
  "templates_created": 0,
  "templates_completed": 0,
  "total_prompts_generated": 0,
  "theme_preference": "system",
  "created_at": "2025-10-20T10:30:00Z"
}
```

## 🎮 Gamification Features

### Credits System
- **Welcome Bonus:** 50 credits on registration
- **Usage:** Consumed by AI services (1-3 credits per operation)
- **Tracking:** Real-time credit balance display

### Level System
- **XP Calculation:** 100 XP = 1 Level
- **Progression:** Automatic level updates
- **Display:** Shows current level in user info

### Daily Streak
- **Tracking:** Consecutive login days
- **Reset:** Breaks if >1 day gap
- **Bonus:** Daily streak displayed on login

### User Ranks
- Prompt Novice (default)
- Prompt Apprentice
- Prompt Expert
- Prompt Master
- (Upgrades based on activity)

## 🧪 Testing Guide

### Test New User Registration

1. Open `http://127.0.0.1:8000/auth/`
2. Click "Sign Up" tab
3. Enter test data:
   ```
   Username: testuser123
   Email: testuser123@example.com
   Password: TestPass123!
   Confirm: TestPass123!
   ```
4. Click "Create Account"
5. Verify:
   - ✅ Success message appears
   - ✅ User info displayed (username, email, credits=150)
   - ✅ JWT token shown
   - ✅ localStorage contains tokens
   - ✅ "Go to Dashboard" button works

### Test Existing User Login

1. Open `http://127.0.0.1:8000/auth/`
2. Click "Sign In" tab
3. Enter credentials:
   ```
   Email: testuser123@example.com
   Password: TestPass123!
   ```
4. Click "Sign In"
5. Verify:
   - ✅ Success message appears
   - ✅ User info displayed
   - ✅ Daily streak shown
   - ✅ JWT token updated in localStorage

### Test Protected Endpoint

1. Login via auth page
2. Go to `http://127.0.0.1:8000/ai-test/optimizer/`
3. Enter test prompt:
   ```
   Write a blog post about AI
   ```
4. Submit form
5. Verify:
   - ✅ Request includes Authorization header
   - ✅ API responds with optimized prompt
   - ✅ No 401 Unauthorized errors

### Test Token Management

1. Go to `http://127.0.0.1:8000/ai-test/`
2. Verify "JWT Token: Active" status
3. Click "Copy JWT" button
4. Verify token copied to clipboard
5. Click "Logout" button
6. Verify:
   - ✅ Tokens cleared from localStorage
   - ✅ Page reloads showing "Not Set"
   - ✅ "Sign In / Sign Up" button appears

## 🐛 Common Issues & Solutions

### Issue: "Invalid credentials" on login
**Solution:** 
- Check email/username is correct
- Verify password matches registration
- Ensure user exists in database

### Issue: Token not being sent with requests
**Solution:**
- Check localStorage contains 'access_token'
- Verify Authorization header format: `Bearer <token>`
- Clear browser cache and re-authenticate

### Issue: 401 Unauthorized on protected endpoints
**Solution:**
- Token may be expired - login again
- Check token format in Authorization header
- Verify JWT_SECRET_KEY matches in settings

### Issue: Registration fails with validation errors
**Solution:**
- Username: Must be unique, min 3 characters
- Email: Must be valid and unique
- Password: Min 8 characters, not too common
- Password2: Must match password

### Issue: "Already Authenticated" shown incorrectly
**Solution:**
- Clear localStorage: `localStorage.clear()`
- Refresh page
- Re-login if needed

## 🔄 Token Refresh Flow

```javascript
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const response = await fetch('http://127.0.0.1:8000/api/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken })
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    return data.access;
  } else {
    // Refresh token expired - need to login again
    logout();
    throw new Error('Refresh token expired');
  }
}

// Use in API calls with retry logic
async function authenticatedFetch(url, options = {}) {
  let token = localStorage.getItem('access_token');
  
  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };
  
  let response = await fetch(url, options);
  
  // If 401, try refreshing token
  if (response.status === 401) {
    token = await refreshAccessToken();
    options.headers['Authorization'] = `Bearer ${token}`;
    response = await fetch(url, options);
  }
  
  return response;
}
```

## 📝 Integration Checklist

- [x] Auth page created at `/auth/`
- [x] JWT storage in localStorage
- [x] Dashboard shows auth status
- [x] Copy/logout token buttons
- [x] User info display
- [x] Welcome bonus (50 credits)
- [x] Daily streak tracking
- [x] Validation error handling
- [x] Success message display
- [x] Automatic token injection in test pages
- [ ] Token refresh implementation (optional)
- [ ] Remember me functionality (optional)
- [ ] Social auth integration (optional)

## 🎉 Summary

Your authentication system is now fully integrated with:

- ✅ Professional sign-in/sign-up interface
- ✅ Automatic JWT token management
- ✅ localStorage persistence
- ✅ Dashboard integration with auth status
- ✅ User gamification (credits, levels, streaks)
- ✅ Copy/logout functionality
- ✅ Seamless AI services integration

**Start Testing:** http://127.0.0.1:8000/auth/
