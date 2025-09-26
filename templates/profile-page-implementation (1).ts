// 🏛️ Profile Page Implementation - Sprint 2
// File: src/app/profile/page.tsx

'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Card } from '@/components/ui/card-unified';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input-unified';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  User, 
  Settings, 
  Crown, 
  Trophy, 
  CreditCard, 
  Shield, 
  Bell, 
  Palette,
  Globe,
  Eye,
  Camera,
  Save,
  Loader2,
  Star,
  Zap,
  Target,
  Calendar,
  TrendingUp,
  Award,
  BookOpen
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { authService } from '@/lib/api/auth';

// 🏺 Profile Store
interface ProfileState {
  // User data
  profile: UserProfile | null;
  isLoading: boolean;
  isUpdating: boolean;
  
  // Form states
  personalInfo: PersonalInfoForm;
  preferences: PreferencesForm;
  hasUnsavedChanges: boolean;
  
  // Actions
  setProfile: (profile: UserProfile) => void;
  updatePersonalInfo: (info: Partial<PersonalInfoForm>) => void;
  updatePreferences: (prefs: Partial<PreferencesForm>) => void;
  setLoading: (loading: boolean) => void;
  setUpdating: (updating: boolean) => void;
  resetChanges: () => void;
}

interface UserProfile {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar: string | null;
  avatar_url: string;
  bio: string;
  date_joined: string;
  last_login: string | null;
  credits: number;
  level: number;
  experience_points: number;
  daily_streak: number;
  user_rank: string;
  rank_info: string;
  next_level_xp: string;
  is_premium: boolean;
  premium_expires_at: string | null;
  theme_preference: 'light' | 'dark' | 'system';
  language_preference: string;
  ai_assistance_enabled: boolean;
  analytics_enabled: boolean;
  templates_created: number;
  templates_completed: number;
  total_prompts_generated: number;
  completion_rate: string;
  created_at: string;
  updated_at: string;
}

interface PersonalInfoForm {
  first_name: string;
  last_name: string;
  bio: string;
  avatar?: File | null;
}

interface PreferencesForm {
  theme_preference: 'light' | 'dark' | 'system';
  language_preference: string;
  ai_assistance_enabled: boolean;
  analytics_enabled: boolean;
}

const useProfileStore = create<ProfileState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    profile: null,
    isLoading: true,
    isUpdating: false,
    personalInfo: {
      first_name: '',
      last_name: '',
      bio: '',
      avatar: null,
    },
    preferences: {
      theme_preference: 'system',
      language_preference: 'en',
      ai_assistance_enabled: true,
      analytics_enabled: true,
    },
    hasUnsavedChanges: false,
    
    // Actions
    setProfile: (profile) => {
      set({
        profile,
        personalInfo: {
          first_name: profile.first_name,
          last_name: profile.last_name,
          bio: profile.bio,
          avatar: null,
        },
        preferences: {
          theme_preference: profile.theme_preference,
          language_preference: profile.language_preference,
          ai_assistance_enabled: profile.ai_assistance_enabled,
          analytics_enabled: profile.analytics_enabled,
        },
        isLoading: false,
      });
    },
    
    updatePersonalInfo: (info) => {
      set(state => ({
        personalInfo: { ...state.personalInfo, ...info },
        hasUnsavedChanges: true,
      }));
    },
    
    updatePreferences: (prefs) => {
      set(state => ({
        preferences: { ...state.preferences, ...prefs },
        hasUnsavedChanges: true,
      }));
    },
    
    setLoading: (isLoading) => set({ isLoading }),
    setUpdating: (isUpdating) => set({ isUpdating }),
    
    resetChanges: () => {
      const { profile } = get();
      if (profile) {
        set({
          personalInfo: {
            first_name: profile.first_name,
            last_name: profile.last_name,
            bio: profile.bio,
            avatar: null,
          },
          preferences: {
            theme_preference: profile.theme_preference,
            language_preference: profile.language_preference,
            ai_assistance_enabled: profile.ai_assistance_enabled,
            analytics_enabled: profile.analytics_enabled,
          },
          hasUnsavedChanges: false,
        });
      }
    },
  }))
);

// 🎖️ User Stats Component
const UserStats = ({ profile }: { profile: UserProfile }) => {
  const nextLevelProgress = (profile.experience_points / parseInt(profile.next_level_xp)) * 100;
  
  const stats = [
    {
      label: 'Templates Created',
      value: profile.templates_created,
      icon: BookOpen,
      color: 'text-blue-500',
      bg: 'bg-blue-50'
    },
    {
      label: 'Templates Completed',
      value: profile.templates_completed,
      icon: Target,
      color: 'text-green-500',
      bg: 'bg-green-50'
    },
    {
      label: 'Prompts Generated',
      value: profile.total_prompts_generated,
      icon: Zap,
      color: 'text-yellow-500',
      bg: 'bg-yellow-50'
    },
    {
      label: 'Daily Streak',
      value: profile.daily_streak,
      icon: Trophy,
      color: 'text-orange-500',
      bg: 'bg-orange-50'
    }
  ];
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.label} variant="default" className="text-center p-4">
            <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full ${stat.bg} mb-3`}>
              <Icon className={`h-6 w-6 ${stat.color}`} />
            </div>
            <div className="text-2xl font-bold text-fg">{stat.value}</div>
            <div className="text-sm text-fg/60">{stat.label}</div>
          </Card>
        );
      })}
    </div>
  );
};

// 🏆 Level & Rank Display
const LevelRankDisplay = ({ profile }: { profile: UserProfile }) => {
  const nextLevelProgress = (profile.experience_points / parseInt(profile.next_level_xp)) * 100;
  
  return (
    <Card variant="temple" className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center">
            <Crown className="h-8 w-8 text-accent" />
          </div>
          <Badge 
            variant="secondary" 
            className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-accent text-white"
          >
            Lv. {profile.level}
          </Badge>
        </div>
        
        <div className="flex-1">
          <h3 className="text-xl font-bold text-fg">{profile.user_rank}</h3>
          <p className="text-sm text-fg/60 mb-2">{profile.rank_info}</p>
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-fg/60">Progress to Level {profile.level + 1}</span>
              <span className="text-fg">{profile.experience_points}/{profile.next_level_xp} XP</span>
            </div>
            <Progress value={nextLevelProgress} className="h-2" />
          </div>
        </div>
      </div>
      
      {profile.is_premium && (
        <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-accent/10 to-accent/5 rounded-lg">
          <Star className="h-5 w-5 text-accent" />
          <div>
            <span className="font-medium text-fg">Premium Member</span>
            {profile.premium_expires_at && (
              <div className="text-sm text-fg/60">
                Expires: {new Date(profile.premium_expires_at).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  );
};

// 👤 Personal Information Tab
const PersonalInfoTab = () => {
  const { 
    profile, 
    personalInfo, 
    updatePersonalInfo, 
    isUpdating 
  } = useProfileStore();
  
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  
  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      updatePersonalInfo({ avatar: file });
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setAvatarPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };
  
  if (!profile) return null;
  
  return (
    <div className="space-y-6">
      {/* Avatar Section */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4">Profile Picture</h3>
        <div className="flex items-center gap-6">
          <div className="relative">
            <Avatar className="w-20 h-20">
              <AvatarImage 
                src={avatarPreview || profile.avatar_url} 
                alt={profile.username} 
              />
              <AvatarFallback className="text-lg">
                {profile.first_name[0]}{profile.last_name[0]}
              </AvatarFallback>
            </Avatar>
            <label className="absolute bottom-0 right-0 bg-accent text-white rounded-full p-2 cursor-pointer hover:bg-accent/80 transition-colors">
              <Camera className="h-4 w-4" />
              <input
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
              />
            </label>
          </div>
          <div>
            <h4 className="font-medium text-fg">{profile.username}</h4>
            <p className="text-sm text-fg/60">Upload a new profile picture</p>
          </div>
        </div>
      </Card>
      
      {/* Basic Information */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4">Basic Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="first_name">First Name</Label>
            <Input
              id="first_name"
              value={personalInfo.first_name}
              onChange={(e) => updatePersonalInfo({ first_name: e.target.value })}
              disabled={isUpdating}
            />
          </div>
          <div>
            <Label htmlFor="last_name">Last Name</Label>
            <Input
              id="last_name"
              value={personalInfo.last_name}
              onChange={(e) => updatePersonalInfo({ last_name: e.target.value })}
              disabled={isUpdating}
            />
          </div>
        </div>
        
        <div className="mt-4">
          <Label htmlFor="bio">Bio</Label>
          <Textarea
            id="bio"
            value={personalInfo.bio}
            onChange={(e) => updatePersonalInfo({ bio: e.target.value })}
            placeholder="Tell us about yourself..."
            disabled={isUpdating}
            rows={3}
          />
          <div className="text-xs text-fg/60 mt-1">
            {personalInfo.bio.length}/500 characters
          </div>
        </div>
      </Card>
      
      {/* Account Information */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4">Account Information</h3>
        <div className="space-y-4">
          <div>
            <Label>Username</Label>
            <Input value={profile.username} disabled />
          </div>
          <div>
            <Label>Email</Label>
            <Input value={profile.email} disabled />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Member Since</Label>
              <Input 
                value={new Date(profile.date_joined).toLocaleDateString()} 
                disabled 
              />
            </div>
            <div>
              <Label>Last Login</Label>
              <Input 
                value={profile.last_login ? new Date(profile.last_login).toLocaleDateString() : 'Never'} 
                disabled 
              />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

// ⚙️ Preferences Tab
const PreferencesTab = () => {
  const { preferences, updatePreferences, isUpdating } = useProfileStore();
  
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'ar', name: 'Arabic' },
  ];
  
  return (
    <div className="space-y-6">
      {/* Appearance */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4 flex items-center gap-2">
          <Palette className="h-5 w-5" />
          Appearance
        </h3>
        <div className="space-y-4">
          <div>
            <Label>Theme</Label>
            <div className="flex gap-2 mt-2">
              {[
                { value: 'light', label: 'Light' },
                { value: 'dark', label: 'Dark' },
                { value: 'system', label: 'System' }
              ].map((theme) => (
                <Button
                  key={theme.value}
                  variant={preferences.theme_preference === theme.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => updatePreferences({ theme_preference: theme.value as any })}
                  disabled={isUpdating}
                >
                  {theme.label}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </Card>
      
      {/* Language & Region */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4 flex items-center gap-2">
          <Globe className="h-5 w-5" />
          Language & Region
        </h3>
        <div>
          <Label htmlFor="language">Language</Label>
          <select
            id="language"
            value={preferences.language_preference}
            onChange={(e) => updatePreferences({ language_preference: e.target.value })}
            className="w-full mt-2 p-2 border border-border rounded-lg bg-card text-fg"
            disabled={isUpdating}
          >
            {languages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>
      </Card>
      
      {/* AI Assistance */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5" />
          AI Assistance
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Enable AI Suggestions</Label>
              <p className="text-sm text-fg/60">Get AI-powered suggestions while creating prompts</p>
            </div>
            <Switch
              checked={preferences.ai_assistance_enabled}
              onCheckedChange={(checked) => updatePreferences({ ai_assistance_enabled: checked })}
              disabled={isUpdating}
            />
          </div>
        </div>
      </Card>
      
      {/* Privacy */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Privacy
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Analytics</Label>
              <p className="text-sm text-fg/60">Allow us to collect anonymous usage data to improve the service</p>
            </div>
            <Switch
              checked={preferences.analytics_enabled}
              onCheckedChange={(checked) => updatePreferences({ analytics_enabled: checked })}
              disabled={isUpdating}
            />
          </div>
        </div>
      </Card>
    </div>
  );
};

// 💳 Subscription Tab
const SubscriptionTab = () => {
  const { profile } = useProfileStore();
  
  if (!profile) return null;
  
  return (
    <div className="space-y-6">
      {/* Current Plan */}
      <Card variant="temple" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4 flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          Current Plan
        </h3>
        
        <div className="flex items-center justify-between p-4 bg-gradient-to-r from-accent/10 to-accent/5 rounded-lg">
          <div>
            <h4 className="font-semibold text-fg">
              {profile.is_premium ? 'Premium' : 'Free'} Plan
            </h4>
            <p className="text-sm text-fg/60">
              {profile.is_premium 
                ? 'Unlimited access to all features'
                : 'Limited access to basic features'
              }
            </p>
          </div>
          {profile.is_premium && (
            <Badge variant="secondary" className="bg-accent text-white">
              Active
            </Badge>
          )}
        </div>
        
        {!profile.is_premium && (
          <div className="mt-4">
            <Button className="w-full">
              <Crown className="h-4 w-4 mr-2" />
              Upgrade to Premium
            </Button>
          </div>
        )}
      </Card>
      
      {/* Credits */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4">Credit Balance</h3>
        <div className="text-center space-y-2">
          <div className="text-3xl font-bold text-accent">{profile.credits}</div>
          <div className="text-sm text-fg/60">Available Credits</div>
          {profile.credits < 10 && (
            <Button variant="outline" size="sm">
              Purchase More Credits
            </Button>
          )}
        </div>
      </Card>
      
      {/* Usage Statistics */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4">Usage This Month</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-fg/60">Templates Created</span>
            <span className="font-medium">{profile.templates_created}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-fg/60">Prompts Generated</span>
            <span className="font-medium">{profile.total_prompts_generated}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-fg/60">Completion Rate</span>
            <span className="font-medium">{profile.completion_rate}%</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

// 🏛️ Main Profile Page Component
export default function ProfilePage() {
  const {
    profile,
    isLoading,
    isUpdating,
    personalInfo,
    preferences,
    hasUnsavedChanges,
    setProfile,
    setUpdating,
    resetChanges,
  } = useProfileStore();
  
  const queryClient = useQueryClient();
  
  // Fetch user profile
  const { data: profileData, isLoading: profileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => authService.getProfile(),
    onSuccess: (data) => {
      setProfile(data);
    },
  });
  
  // Update profile mutation
  const updateMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      
      // Add personal info
      formData.append('first_name', personalInfo.first_name);
      formData.append('last_name', personalInfo.last_name);
      formData.append('bio', personalInfo.bio);
      
      // Add preferences
      formData.append('theme_preference', preferences.theme_preference);
      formData.append('language_preference', preferences.language_preference);
      formData.append('ai_assistance_enabled', preferences.ai_assistance_enabled.toString());
      formData.append('analytics_enabled', preferences.analytics_enabled.toString());
      
      // Add avatar if changed
      if (personalInfo.avatar) {
        formData.append('avatar', personalInfo.avatar);
      }
      
      return authService.updateProfile(Object.fromEntries(formData));
    },
    onMutate: () => setUpdating(true),
    onSuccess: (data) => {
      setProfile(data);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      toast.success('Profile updated successfully!');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update profile');
    },
    onSettled: () => setUpdating(false),
  });
  
  const handleSave = () => {
    updateMutation.mutate();
  };
  
  const handleReset = () => {
    resetChanges();
    toast.success('Changes discarded');
  };
  
  if (profileLoading || isLoading) {
    return (
      <div className="temple-background min-h-screen p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
          </div>
        </div>
      </div>
    );
  }
  
  if (!profile) {
    return (
      <div className="temple-background min-h-screen p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold text-fg">Profile Not Found</h1>
            <p className="text-fg/60">Unable to load your profile information.</p>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="temple-background min-h-screen p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-fg flex items-center justify-center gap-3">
            <User className="h-8 w-8 text-accent" />
            Profile Settings
          </h1>
          <p className="text-fg/70">
            Manage your account settings and preferences
          </p>
        </div>
        
        {/* Level & Stats Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <UserStats profile={profile} />
          </div>
          <div>
            <LevelRankDisplay profile={profile} />
          </div>
        </div>
        
        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <Tabs defaultValue="personal" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="personal">Personal</TabsTrigger>
                <TabsTrigger value="preferences">Preferences</TabsTrigger>
                <TabsTrigger value="subscription">Subscription</TabsTrigger>
              </TabsList>
              
              <TabsContent value="personal">
                <PersonalInfoTab />
              </TabsContent>
              
              <TabsContent value="preferences">
                <PreferencesTab />
              </TabsContent>
              
              <TabsContent value="subscription">
                <SubscriptionTab />
              </TabsContent>
            </Tabs>
          </div>
          
          {/* Save Panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-6">
              <Card variant="temple" padding="lg">
                <h3 className="text-lg font-semibold text-fg mb-4">Changes</h3>
                
                {hasUnsavedChanges ? (
                  <div className="space-y-3">
                    <div className="text-sm text-fg/60">
                      You have unsaved changes
                    </div>
                    <div className="space-y-2">
                      <Button
                        onClick={handleSave}
                        disabled={isUpdating}
                        className="w-full"
                      >
                        {isUpdating ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Save className="h-4 w-4 mr-2" />
                        )}
                        Save Changes
                      </Button>
                      <Button
                        onClick={handleReset}
                        variant="outline"
                        disabled={isUpdating}
                        className="w-full"
                      >
                        Discard Changes
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-sm text-fg/60">
                    All changes saved
                  </div>
                )}
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}