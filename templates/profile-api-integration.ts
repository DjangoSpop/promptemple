// 🏛️ Profile Page API Integration - Sprint 2 Supporting Files

// File: src/hooks/useProfile.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '@/lib/api/auth';
import { toast } from 'react-hot-toast';

interface ProfileUpdateData {
  first_name?: string;
  last_name?: string;
  bio?: string;
  avatar?: File;
  theme_preference?: 'light' | 'dark' | 'system';
  language_preference?: string;
  ai_assistance_enabled?: boolean;
  analytics_enabled?: boolean;
}

interface PasswordChangeData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export const useProfile = () => {
  const queryClient = useQueryClient();

  // Get current user profile
  const profileQuery = useQuery({
    queryKey: ['profile', 'current'],
    queryFn: () => authService.getProfile(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  // Get user statistics
  const statsQuery = useQuery({
    queryKey: ['profile', 'stats'],
    queryFn: () => authService.getUserStats(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: (data: ProfileUpdateData) => authService.updateProfile(data),
    onSuccess: (updatedProfile) => {
      queryClient.setQueryData(['profile', 'current'], updatedProfile);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      toast.success('Profile updated successfully!');
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to update profile';
      toast.error(errorMessage);
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: (data: PasswordChangeData) => {
      if (data.new_password !== data.confirm_password) {
        throw new Error('New passwords do not match');
      }
      return authService.changePassword({
        old_password: data.old_password,
        new_password: data.new_password,
      });
    },
    onSuccess: () => {
      toast.success('Password changed successfully!');
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to change password';
      toast.error(errorMessage);
    },
  });

  return {
    profile: profileQuery.data,
    stats: statsQuery.data,
    isLoading: profileQuery.isLoading,
    isError: profileQuery.isError,
    error: profileQuery.error,
    updateProfile: updateProfileMutation.mutate,
    changePassword: changePasswordMutation.mutate,
    isUpdating: updateProfileMutation.isPending,
    isChangingPassword: changePasswordMutation.isPending,
    refetch: () => {
      profileQuery.refetch();
      statsQuery.refetch();
    },
  };
};

// File: src/components/profile/PasswordChangeModal.tsx
import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input-unified';
import { Label } from '@/components/ui/label';
import { useProfile } from '@/hooks/useProfile';
import { Lock, Eye, EyeOff } from 'lucide-react';

export const PasswordChangeModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showPasswords, setShowPasswords] = useState({
    old: false,
    new: false,
    confirm: false,
  });
  
  const [formData, setFormData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  const { changePassword, isChangingPassword } = useProfile();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    changePassword(formData, {
      onSuccess: () => {
        setIsOpen(false);
        setFormData({
          old_password: '',
          new_password: '',
          confirm_password: '',
        });
      },
    });
  };

  const togglePasswordVisibility = (field: keyof typeof showPasswords) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field],
    }));
  };

  const isValid = formData.old_password.length >= 8 && 
                  formData.new_password.length >= 8 && 
                  formData.new_password === formData.confirm_password;

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Lock className="h-4 w-4 mr-2" />
          Change Password
        </Button>
      </DialogTrigger>
      
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Change Password</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="old_password">Current Password</Label>
            <div className="relative">
              <Input
                id="old_password"
                type={showPasswords.old ? 'text' : 'password'}
                value={formData.old_password}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  old_password: e.target.value,
                }))}
                required
                minLength={8}
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('old')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-fg/50"
              >
                {showPasswords.old ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          
          <div>
            <Label htmlFor="new_password">New Password</Label>
            <div className="relative">
              <Input
                id="new_password"
                type={showPasswords.new ? 'text' : 'password'}
                value={formData.new_password}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  new_password: e.target.value,
                }))}
                required
                minLength={8}
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('new')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-fg/50"
              >
                {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="text-xs text-fg/60 mt-1">
              Must be at least 8 characters long
            </p>
          </div>
          
          <div>
            <Label htmlFor="confirm_password">Confirm New Password</Label>
            <div className="relative">
              <Input
                id="confirm_password"
                type={showPasswords.confirm ? 'text' : 'password'}
                value={formData.confirm_password}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  confirm_password: e.target.value,
                }))}
                required
                minLength={8}
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('confirm')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-fg/50"
              >
                {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {formData.confirm_password && formData.new_password !== formData.confirm_password && (
              <p className="text-xs text-red-500 mt-1">
                Passwords do not match
              </p>
            )}
          </div>
          
          <div className="flex gap-2 pt-4">
            <Button
              type="submit"
              disabled={!isValid || isChangingPassword}
              className="flex-1"
            >
              {isChangingPassword ? 'Changing...' : 'Change Password'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
              disabled={isChangingPassword}
            >
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// File: src/components/profile/DeleteAccountModal.tsx
import React, { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input-unified';
import { AlertTriangle, Trash2 } from 'lucide-react';
import { toast } from 'react-hot-toast';

export const DeleteAccountModal = ({ username }: { username: string }) => {
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (confirmText !== username) {
      toast.error('Username confirmation does not match');
      return;
    }

    setIsDeleting(true);
    try {
      // Call delete account API
      await fetch('/api/v2/auth/delete-account/', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      
      toast.success('Account deleted successfully');
      // Redirect to homepage
      window.location.href = '/';
    } catch (error) {
      toast.error('Failed to delete account');
      setIsDeleting(false);
    }
  };

  const isValid = confirmText === username;

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline" size="sm" className="text-red-600 border-red-200 hover:bg-red-50">
          <Trash2 className="h-4 w-4 mr-2" />
          Delete Account
        </Button>
      </AlertDialogTrigger>
      
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            Delete Account
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-3">
            <p>
              This action cannot be undone. This will permanently delete your account and remove all of your data from our servers.
            </p>
            <div>
              <p className="font-medium mb-2">Type <code className="bg-gray-100 px-1 rounded">{username}</code> to confirm:</p>
              <Input
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder={username}
              />
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={!isValid || isDeleting}
            className="bg-red-600 hover:bg-red-700"
          >
            {isDeleting ? 'Deleting...' : 'Delete Account'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

// File: src/components/profile/ExportDataButton.tsx
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Download, FileText, Database } from 'lucide-react';
import { toast } from 'react-hot-toast';

export const ExportDataButton = () => {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: 'json' | 'csv') => {
    setIsExporting(true);
    try {
      const response = await fetch(`/api/v2/auth/export-data/?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `promptcraft-data.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast.success(`Data exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export data');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('json')}
        disabled={isExporting}
      >
        <FileText className="h-4 w-4 mr-2" />
        Export JSON
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('csv')}
        disabled={isExporting}
      >
        <Database className="h-4 w-4 mr-2" />
        Export CSV
      </Button>
    </div>
  );
};

// File: src/app/profile/layout.tsx
export default function ProfileLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="temple-background min-h-screen">
      {children}
    </div>
  );
}

// File: src/components/profile/ProfileSidebar.tsx
import React from 'react';
import { Card } from '@/components/ui/card-unified';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  User, 
  Settings, 
  CreditCard, 
  Shield, 
  Download, 
  Trash2,
  Bell
} from 'lucide-react';
import { PasswordChangeModal } from './PasswordChangeModal';
import { DeleteAccountModal } from './DeleteAccountModal';
import { ExportDataButton } from './ExportDataButton';

interface ProfileSidebarProps {
  profile: any;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const ProfileSidebar = ({ profile, activeTab, onTabChange }: ProfileSidebarProps) => {
  const menuItems = [
    {
      id: 'personal',
      label: 'Personal Info',
      icon: User,
      description: 'Basic information and avatar'
    },
    {
      id: 'preferences',
      label: 'Preferences',
      icon: Settings,
      description: 'Theme, language, and AI settings'
    },
    {
      id: 'subscription',
      label: 'Subscription',
      icon: CreditCard,
      description: 'Plan and billing information'
    },
    {
      id: 'privacy',
      label: 'Privacy',
      icon: Shield,
      description: 'Data and privacy settings'
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: Bell,
      description: 'Email and push preferences'
    }
  ];

  return (
    <div className="space-y-4">
      {/* Navigation */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4">Settings</h3>
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors ${
                  activeTab === item.id 
                    ? 'bg-accent/10 text-accent' 
                    : 'hover:bg-card/50 text-fg/70'
                }`}
              >
                <Icon className="h-5 w-5 mt-0.5" />
                <div>
                  <div className="font-medium">{item.label}</div>
                  <div className="text-xs text-fg/50">{item.description}</div>
                </div>
              </button>
            );
          })}
        </nav>
      </Card>

      {/* Account Actions */}
      <Card variant="default" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4">Account Actions</h3>
        <div className="space-y-3">
          <PasswordChangeModal />
          <ExportDataButton />
          <DeleteAccountModal username={profile?.username || ''} />
        </div>
      </Card>

      {/* Account Status */}
      <Card variant="temple" padding="lg">
        <h3 className="text-lg font-semibold text-fg mb-4">Account Status</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-fg/60">Status</span>
            <Badge variant={profile?.is_premium ? "default" : "secondary"}>
              {profile?.is_premium ? 'Premium' : 'Free'}
            </Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-fg/60">Level</span>
            <span className="font-medium">{profile?.level || 1}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-fg/60">Credits</span>
            <span className="font-medium text-accent">{profile?.credits || 0}</span>
          </div>
        </div>
      </Card>
    </div>
  );
};