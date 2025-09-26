// 🏛️ Profile Page Implementation - Sprint 2
// File: src/pages/profile/index.tsx

import React, { useState } from 'react';
import { NextPage } from 'next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/lib/api/auth';
import { Card } from '@/components/ui/card-unified';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { TempleNavbar } from '@/components/TempleNavbar';
import { 
  User, 
  Edit3, 
  Crown, 
  TrendingUp, 
  Calendar, 
  Mail, 
  Shield, 
  Palette,
  Globe,
  Bot,
  BarChart3,
  CreditCard,
  Award,
  Settings,
  Camera,
  Save,
  X
} from 'lucide-react';
import toast from 'react-hot-toast';

// Profile Statistics Component
const ProfileStats = ({ user }: { user: any }) => {
  const stats = [
    {
      label: 'Templates Created',
      value: user.templates_created,
      icon: Edit3,
      color: 'text-blue-500'
    },
    {
      label: 'Templates Completed',
      value: user.templates_completed,
      icon: Award,
      color: 'text-green-500'
    },
    {
      label: 'Total Prompts',
      value: user.total_prompts_generated,
      icon: BarChart3,
      color: 'text-purple-500'
    },
    {
      label: 'Completion Rate',
      value: `${user.completion_rate}%`,
      icon: TrendingUp,
      color: 'text-orange-500'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.label} variant="default" className="p-4 text-center">
            <Icon className={`h-8 w-8 mx-auto mb-2 ${stat.color}`} />
            <div className="text-2xl font-bold text-fg">{stat.value}</div>
            <div className="text-xs text-fg/60 mt-1">{stat.label}</div>
          </Card>
        );
      })}
    </div>
  );
};

// User Level Progress Component
const UserLevelProgress = ({ user }: { user: any }) => {
  const currentXP = user.experience_points;
  const nextLevelXP = parseInt(user.next_level_xp);
  const progressPercent = (currentXP / nextLevelXP) * 100;

  return (
    <Card variant="temple" className="p-6">
      <div className="flex items-center gap-4 mb-4">
        <div className="p-3 bg-accent/20 rounded-full">
          <Crown className="h-6 w-6 text-accent" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-fg">Level {user.level}</h3>
          <p className="text-sm text-fg/70">{user.user_rank}</p>
        </div>
        <div className="ml-auto">
          <Badge variant="secondary" className="bg-accent/20 text-accent">
            {user.daily_streak} day streak
          </Badge>
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-fg/70">Experience Points</span>
          <span className="text-fg">{currentXP.toLocaleString()} / {nextLevelXP.toLocaleString()}</span>
        </div>
        <Progress value={progressPercent} className="h-3" />
        <p className="text-xs text-fg/60 mt-2">{user.rank_info}</p>
      </div>
    </Card>
  );
};

// Subscription Panel Component
const SubscriptionPanel = ({ user }: { user: any }) => {
  return (
    <Card variant="temple" className="p-6">
      <div className="flex items-center gap-4 mb-4">
        <div className="p-3 bg-accent/20 rounded-full">
          <CreditCard className="h-6 w-6 text-accent" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-fg">
            {user.is_premium ? 'Premium Account' : 'Free Account'}
          </h3>
          <p className="text-sm text-fg/70">
            {user.is_premium ? 'Premium features enabled' : 'Upgrade for more features'}
          </p>
        </div>
        <div className="ml-auto">
          {user.is_premium ? (
            <Badge className="bg-gradient-to-r from-accent to-yellow-500">
              Premium
            </Badge>
          ) : (
            <Button size="sm">Upgrade</Button>
          )}
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-2xl font-bold text-fg">{user.credits}</div>
          <div className="text-xs text-fg/60">Credits Available</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-fg">
            {user.premium_expires_at ? new Date(user.premium_expires_at).toLocaleDateString() : 'N/A'}
          </div>
          <div className="text-xs text-fg/60">
            {user.is_premium ? 'Expires' : 'Not Premium'}
          </div>
        </div>
      </div>
    </Card>
  );
};

// Profile Form Component
const ProfileForm = ({ user, onSave }: { user: any, onSave: () => void }) => {
  const [formData, setFormData] = useState({
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    bio: user.bio || '',
    theme_preference: user.theme_preference || 'light',
    language_preference: user.language_preference || 'en',
    ai_assistance_enabled: user.ai_assistance_enabled ?? true,
    analytics_enabled: user.analytics_enabled ?? true,
  });

  const [isEditing, setIsEditing] = useState(false);
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (data: any) => authService.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'profile'] });
      setIsEditing(false);
      onSave();
      toast.success('Profile updated successfully!');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update profile');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  const handleCancel = () => {
    setFormData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      bio: user.bio || '',
      theme_preference: user.theme_preference || 'light',
      language_preference: user.language_preference || 'en',
      ai_assistance_enabled: user.ai_assistance_enabled ?? true,
      analytics_enabled: user.analytics_enabled ?? true,
    });
    setIsEditing(false);
  };

  return (
    <Card variant="temple" className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-fg">Profile Information</h3>
        {!isEditing ? (
          <Button onClick={() => setIsEditing(true)} size="sm" variant="outline">
            <Edit3 className="h-4 w-4 mr-2" />
            Edit
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button 
              onClick={handleSubmit} 
              size="sm" 
              disabled={updateMutation.isPending}
            >
              <Save className="h-4 w-4 mr-2" />
              {updateMutation.isPending ? 'Saving...' : 'Save'}
            </Button>
            <Button onClick={handleCancel} size="sm" variant="outline">
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-fg mb-1">
              First Name
            </label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              disabled={!isEditing}
              className="w-full p-3 border border-border rounded-lg bg-card text-fg disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-fg mb-1">
              Last Name
            </label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              disabled={!isEditing}
              className="w-full p-3 border border-border rounded-lg bg-card text-fg disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-fg mb-1">
            Bio
          </label>
          <textarea
            value={formData.bio}
            onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
            disabled={!isEditing}
            rows={3}
            className="w-full p-3 border border-border rounded-lg bg-card text-fg disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent resize-none"
            placeholder="Tell us about yourself..."
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-fg mb-1">
              <Palette className="h-4 w-4 inline mr-1" />
              Theme Preference
            </label>
            <select
              value={formData.theme_preference}
              onChange={(e) => setFormData({ ...formData, theme_preference: e.target.value })}
              disabled={!isEditing}
              className="w-full p-3 border border-border rounded-lg bg-card text-fg disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="system">System</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-fg mb-1">
              <Globe className="h-4 w-4 inline mr-1" />
              Language
            </label>
            <select
              value={formData.language_preference}
              onChange={(e) => setFormData({ ...formData, language_preference: e.target.value })}
              disabled={!isEditing}
              className="w-full p-3 border border-border rounded-lg bg-card text-fg disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="ar">العربية</option>
            </select>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-accent" />
              <span className="text-sm font-medium text-fg">AI Assistance</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.ai_assistance_enabled}
                onChange={(e) => setFormData({ ...formData, ai_assistance_enabled: e.target.checked })}
                disabled={!isEditing}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-card border border-border peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-accent" />
              <span className="text-sm font-medium text-fg">Analytics</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.analytics_enabled}
                onChange={(e) => setFormData({ ...formData, analytics_enabled: e.target.checked })}
                disabled={!isEditing}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-card border border-border peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
            </label>
          </div>
        </div>
      </form>
    </Card>
  );
};

// Avatar Upload Component
const AvatarUpload = ({ user, onUpdate }: { user: any, onUpdate: () => void }) => {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type and size
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      toast.error('Image size must be less than 5MB');
      return;
    }

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('avatar', file);
      
      await authService.updateProfile(formData);
      onUpdate();
      toast.success('Avatar updated successfully!');
    } catch (error: any) {
      toast.error(error.message || 'Failed to update avatar');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative">
        <div className="w-32 h-32 rounded-full bg-card border-4 border-border overflow-hidden">
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={`${user.first_name} ${user.last_name}`.trim() || user.username}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-accent/20">
              <User className="h-12 w-12 text-accent" />
            </div>
          )}
        </div>
        
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}