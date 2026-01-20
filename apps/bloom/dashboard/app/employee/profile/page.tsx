'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import PageHeader from '@/components/PageHeader';
import Card from '@/components/Card';
import Input from '@/components/Input';
import Select from '@/components/Select';
import Button from '@/components/Button';
import LoadingSpinner from '@/components/LoadingSpinner';
import AlertBanner from '@/components/AlertBanner';

interface ProfileData {
  name: string;
  email: string;
  department: string;
  role: string;
  manager: string;
  start_date: string;
  phone?: string;
  location?: string;
  timezone: string;
  notification_preferences: {
    email: boolean;
    push: boolean;
    evaluation_reminders: boolean;
    feedback_received: boolean;
  };
}

export default function EmployeeProfilePage() {
  const { user: _user } = useAuth();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch('/api/employee/profile');
        const data = await response.json();
        setProfile(data);
      } catch (error) {
        console.error('Failed to fetch profile:', error);
        setError('Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleSave = async () => {
    if (!profile) return;

    setIsSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch('/api/employee/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });

      if (!response.ok) throw new Error('Failed to update profile');

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      setError('Failed to save profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">Profile not found</h2>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Profile"
        description="Manage your personal information and preferences"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'My Evaluations', href: '/employee' },
          { label: 'Profile', href: '/employee/profile' },
        ]}
      />

      {success && (
        <AlertBanner alerts={[{
          id: 'profile-success',
          type: 'success',
          title: 'Success',
          message: 'Profile updated successfully!'
        }]} />
      )}

      {error && (
        <AlertBanner alerts={[{
          id: 'profile-error',
          type: 'error',
          title: 'Error',
          message: error
        }]} />
      )}

      {/* Personal Information */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Personal Information</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <Input
            label="Full Name"
            value={profile.name}
            onChange={(e) => setProfile({ ...profile, name: e.target.value })}
          />
          <Input
            label="Email"
            type="email"
            value={profile.email}
            disabled
          />
          <Input
            label="Phone"
            type="tel"
            value={profile.phone || ''}
            onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
            placeholder="(555) 123-4567"
          />
          <Input
            label="Location"
            value={profile.location || ''}
            onChange={(e) => setProfile({ ...profile, location: e.target.value })}
            placeholder="City, State/Country"
          />
        </div>
      </Card>

      {/* Work Information */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Work Information</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <Input
            label="Department"
            value={profile.department}
            disabled
          />
          <Input
            label="Role"
            value={profile.role}
            disabled
          />
          <Input
            label="Manager"
            value={profile.manager}
            disabled
          />
          <Input
            label="Start Date"
            value={profile.start_date}
            disabled
          />
          <Select
            label="Timezone"
            value={profile.timezone}
            onChange={(value) => setProfile({ ...profile, timezone: String(value) })}
            options={[
              { value: 'America/New_York', label: 'Eastern Time (ET)' },
              { value: 'America/Chicago', label: 'Central Time (CT)' },
              { value: 'America/Denver', label: 'Mountain Time (MT)' },
              { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
              { value: 'UTC', label: 'UTC' },
            ]}
          />
        </div>
      </Card>

      {/* Notification Preferences */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Notification Preferences</h2>
        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={profile.notification_preferences.email}
              onChange={(e) => setProfile({
                ...profile,
                notification_preferences: {
                  ...profile.notification_preferences,
                  email: e.target.checked,
                },
              })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Email Notifications</div>
              <div className="text-sm text-gray-600">Receive updates via email</div>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={profile.notification_preferences.push}
              onChange={(e) => setProfile({
                ...profile,
                notification_preferences: {
                  ...profile.notification_preferences,
                  push: e.target.checked,
                },
              })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Push Notifications</div>
              <div className="text-sm text-gray-600">Receive browser notifications</div>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={profile.notification_preferences.evaluation_reminders}
              onChange={(e) => setProfile({
                ...profile,
                notification_preferences: {
                  ...profile.notification_preferences,
                  evaluation_reminders: e.target.checked,
                },
              })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Evaluation Reminders</div>
              <div className="text-sm text-gray-600">Get reminded about pending evaluations</div>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={profile.notification_preferences.feedback_received}
              onChange={(e) => setProfile({
                ...profile,
                notification_preferences: {
                  ...profile.notification_preferences,
                  feedback_received: e.target.checked,
                },
              })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Feedback Received</div>
              <div className="text-sm text-gray-600">Notify when feedback is available</div>
            </div>
          </label>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex gap-3 justify-end">
        <Button variant="ghost">
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleSave}
          isLoading={isSaving}
        >
          Save Changes
        </Button>
      </div>
    </div>
  );
}
