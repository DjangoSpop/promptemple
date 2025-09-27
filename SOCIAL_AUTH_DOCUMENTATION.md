# Social Authentication System Documentation

## Overview

This document provides comprehensive documentation for the social authentication system implemented in the PromptCraft Django backend. The system supports Google and GitHub OAuth2 authentication with seamless JWT token integration.

## Features

- **OAuth2 Integration**: Google and GitHub social login
- **JWT Token Compatibility**: Returns the same JWT token structure as standard login
- **User Linking**: Link social accounts to existing users or create new ones
- **Avatar Integration**: Automatically fetches and stores social profile pictures
- **Security**: CSRF protection with state parameters, comprehensive error handling
- **Analytics Integration**: Tracks social authentication events
- **Gamification**: Awards welcome bonuses for new social users

## API Endpoints

### 1. Get Provider Information
```
GET /api/v2/auth/social/providers/
```

Returns information about available social authentication providers.

**Response:**
```json
{
  "providers": [
    {
      "name": "google",
      "display_name": "Google",
      "enabled": true,
      "initiate_url": "/api/v2/auth/social/google/initiate/",
      "callback_url": "/api/v2/auth/social/callback/",
      "scopes": ["profile", "email"]
    },
    {
      "name": "github",
      "display_name": "GitHub",
      "enabled": true,
      "initiate_url": "/api/v2/auth/social/github/initiate/",
      "callback_url": "/api/v2/auth/social/callback/",
      "scopes": ["user:email", "read:user"]
    }
  ],
  "callback_url": "/api/v2/auth/social/callback/",
  "frontend_callback_urls": {
    "google": "http://localhost:3000/auth/callback/google",
    "github": "http://localhost:3000/auth/callback/github"
  }
}
```

### 2. Initiate Social Authentication
```
GET /api/v2/auth/social/{provider}/initiate/
```

Initiates the OAuth flow for the specified provider.

**Parameters:**
- `provider`: `google` or `github`
- `redirect_uri` (optional): Frontend callback URL

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...",
  "state": "secure-random-state-string",
  "provider": "google",
  "message": "Redirect user to Google for authorization"
}
```

### 3. Handle OAuth Callback
```
POST /api/v2/auth/social/callback/
```

Processes the OAuth callback and returns JWT tokens.

**Request Body:**
```json
{
  "code": "authorization-code-from-provider",
  "provider": "google",
  "state": "state-parameter-for-csrf-protection",
  "redirect_uri": "http://localhost:3000/auth/callback/google"
}
```

**Response:**
```json
{
  "message": "Social authentication successful",
  "user": {
    "id": "user-uuid",
    "username": "john.doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "avatar_url": "https://example.com/avatar.jpg",
    "social_avatar_url": "https://lh3.googleusercontent.com/...",
    "provider_name": "google",
    "provider_id": "google-user-id",
    "credits": 150,
    "level": 1,
    "daily_streak": 1
  },
  "tokens": {
    "access": "jwt-access-token",
    "refresh": "jwt-refresh-token"
  },
  "is_new_user": true,
  "provider": "google",
  "daily_streak": 1
}
```

### 4. Link Social Account (Authenticated)
```
POST /api/v2/auth/social/link/
```

Links a social account to an existing authenticated user.

**Headers:**
```
Authorization: Bearer <jwt-access-token>
```

**Request Body:**
```json
{
  "code": "authorization-code-from-provider",
  "provider": "github",
  "redirect_uri": "http://localhost:3000/auth/link/github"
}
```

### 5. Unlink Social Account (Authenticated)
```
POST /api/v2/auth/social/unlink/
```

Removes social account linking from the authenticated user.

**Headers:**
```
Authorization: Bearer <jwt-access-token>
```

**Response:**
```json
{
  "message": "Google account unlinked successfully",
  "user": {
    "id": "user-uuid",
    "provider_name": null,
    "provider_id": null,
    "social_avatar_url": null
  }
}
```

## Frontend Integration Guide

### Step 1: Check Available Providers

```javascript
const response = await fetch('/api/v2/auth/social/providers/');
const { providers } = await response.json();
```

### Step 2: Initiate OAuth Flow

```javascript
// Get authorization URL
const response = await fetch(`/api/v2/auth/social/google/initiate/?redirect_uri=${encodeURIComponent(window.location.origin + '/auth/callback/google')}`);
const { auth_url, state } = await response.json();

// Store state for verification
localStorage.setItem('oauth_state', state);

// Redirect user to provider
window.location.href = auth_url;
```

### Step 3: Handle Callback

```javascript
// In your callback route (e.g., /auth/callback/google)
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
const state = urlParams.get('state');
const provider = 'google'; // Extract from route

// Verify state
const storedState = localStorage.getItem('oauth_state');
if (state !== storedState) {
  throw new Error('Invalid state parameter');
}

// Exchange code for tokens
const response = await fetch('/api/v2/auth/social/callback/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    code,
    provider,
    state,
    redirect_uri: window.location.origin + '/auth/callback/google'
  })
});

const data = await response.json();

if (response.ok) {
  // Store tokens
  localStorage.setItem('access_token', data.tokens.access);
  localStorage.setItem('refresh_token', data.tokens.refresh);

  // Redirect to dashboard or welcome page
  if (data.is_new_user) {
    router.push('/welcome');
  } else {
    router.push('/dashboard');
  }
} else {
  // Handle error
  console.error('Social authentication failed:', data.message);
}
```

### Step 4: React Hook Example

```javascript
import { useState, useCallback } from 'react';

export const useSocialAuth = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const initiateSocialAuth = useCallback(async (provider) => {
    try {
      setLoading(true);
      setError(null);

      const redirectUri = `${window.location.origin}/auth/callback/${provider}`;
      const response = await fetch(`/api/v2/auth/social/${provider}/initiate/?redirect_uri=${encodeURIComponent(redirectUri)}`);

      if (!response.ok) {
        throw new Error('Failed to initiate social authentication');
      }

      const { auth_url, state } = await response.json();

      // Store state for verification
      localStorage.setItem(`${provider}_oauth_state`, state);

      // Redirect to provider
      window.location.href = auth_url;

    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, []);

  const handleCallback = useCallback(async (code, provider, state) => {
    try {
      setLoading(true);
      setError(null);

      // Verify state
      const storedState = localStorage.getItem(`${provider}_oauth_state`);
      if (state && state !== storedState) {
        throw new Error('Invalid state parameter - possible CSRF attack');
      }

      const redirectUri = `${window.location.origin}/auth/callback/${provider}`;

      const response = await fetch('/api/v2/auth/social/callback/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          provider,
          state,
          redirect_uri: redirectUri
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Social authentication failed');
      }

      // Clean up stored state
      localStorage.removeItem(`${provider}_oauth_state`);

      return data;

    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    initiateSocialAuth,
    handleCallback,
    loading,
    error
  };
};
```

## Environment Configuration

### Required Environment Variables

```bash
# Google OAuth2 Configuration
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth Configuration
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### Setting Up OAuth Applications

#### Google OAuth2 Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized origins:
   - `http://localhost:3000` (development)
   - `https://yourdomain.com` (production)
7. Add authorized redirect URIs:
   - `http://localhost:3000/auth/callback/google` (development)
   - `https://yourdomain.com/auth/callback/google` (production)

#### GitHub OAuth Setup

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in application details:
   - Application name: Your app name
   - Homepage URL: `https://yourdomain.com`
   - Authorization callback URL: `https://yourdomain.com/auth/callback/github`

## Database Schema Changes

The following fields were added to the User model:

```python
# Social authentication fields
social_avatar_url = models.URLField(
    null=True,
    blank=True,
    help_text="Avatar URL from social provider"
)
provider_id = models.CharField(
    max_length=100,
    null=True,
    blank=True,
    help_text="User ID from social provider"
)
provider_name = models.CharField(
    max_length=50,
    null=True,
    blank=True,
    choices=[
        ('google', 'Google'),
        ('github', 'GitHub'),
    ],
    help_text="Social authentication provider"
)
```

## Security Considerations

1. **State Parameter**: All OAuth flows use a secure random state parameter for CSRF protection
2. **Token Security**: OAuth tokens are not stored; only user information is persisted
3. **Email Verification**: Social accounts are automatically considered email-verified
4. **Password Security**: Social-only accounts have unusable passwords
5. **Account Linking**: Prevents duplicate accounts by linking social accounts to existing email addresses

## Error Handling

The system provides comprehensive error handling for:

- Invalid authorization codes
- Network failures with OAuth providers
- Missing or invalid user information
- Account linking conflicts
- State parameter validation failures

All errors return structured JSON responses with appropriate HTTP status codes.

## Analytics Integration

The system tracks the following events:

- `social_authentication`: When users authenticate via social providers
- `social_account_linked`: When users link social accounts
- `social_account_unlinked`: When users unlink social accounts

## Testing

### Manual Testing

1. Ensure OAuth applications are configured correctly
2. Test both Google and GitHub authentication flows
3. Verify new user creation and existing user linking
4. Test account linking and unlinking functionality
5. Verify JWT token compatibility with existing endpoints

### Automated Testing

The system includes comprehensive unit tests for:

- OAuth handler classes
- API endpoint responses
- User creation and linking logic
- Error handling scenarios

## Troubleshooting

### Common Issues

1. **Invalid Client Error**: Check OAuth client IDs and secrets
2. **Redirect URI Mismatch**: Ensure callback URLs match OAuth app configuration
3. **Email Not Available**: GitHub users with private emails may encounter issues
4. **State Parameter Errors**: Check frontend state storage and verification

### Debug Mode

Set `SOCIAL_AUTH_RAISE_EXCEPTIONS=True` in development to see detailed error messages.

## Production Deployment

1. Update OAuth application URLs to production domains
2. Set proper environment variables
3. Ensure HTTPS is enabled for security
4. Update CORS and CSRF trusted origins
5. Monitor error logs for authentication issues

This completes the comprehensive social authentication system integration with your existing Django backend!