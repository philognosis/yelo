'use client';

import { useState } from 'react';
import { PageHeader } from '../../../components/PageHeader';
import { Card } from '../../../components/Card';
import { Input } from '../../../components/Input';
import { Select } from '../../../components/Select';
import { Button } from '../../../components/Button';
import { AlertBanner } from '../../../components/AlertBanner';

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate save
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSuccess(true);
    setIsSaving(false);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Settings"
        description="Configure global evaluation system settings"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'HR Dashboard', href: '/hr' },
          { label: 'Settings', href: '/hr/settings' },
        ]}
      />

      {success && (
        <AlertBanner type="success" message="Settings saved successfully!" />
      )}

      {/* General Settings */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">General Settings</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <Input
            label="Company Name"
            defaultValue="Acme Corporation"
          />

          <Input
            label="Evaluation Cycle Prefix"
            defaultValue="Q"
            placeholder="e.g., Q, FY, Period"
          />

          <Select
            label="Default Rating Scale"
            defaultValue="5"
            options={[
              { value: '3', label: '3-Point Scale' },
              { value: '5', label: '5-Point Scale' },
              { value: '10', label: '10-Point Scale' },
            ]}
          />

          <Select
            label="Timezone"
            defaultValue="America/New_York"
            options={[
              { value: 'America/New_York', label: 'Eastern Time (ET)' },
              { value: 'America/Chicago', label: 'Central Time (CT)' },
              { value: 'America/Denver', label: 'Mountain Time (MT)' },
              { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
            ]}
          />
        </div>
      </Card>

      {/* Evaluation Settings */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Evaluation Settings</h2>
        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Enable Peer Reviews</div>
              <div className="text-sm text-gray-600">Allow employees to receive feedback from peers</div>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Enable Self-Evaluations</div>
              <div className="text-sm text-gray-600">Require employees to complete self-assessments</div>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Enable AI Draft Assistance</div>
              <div className="text-sm text-gray-600">Provide AI-generated draft evaluations for managers</div>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Enable Committee Reviews</div>
              <div className="text-sm text-gray-600">Require committee calibration for final ratings</div>
            </div>
          </label>

          <div className="grid md:grid-cols-2 gap-6 mt-6">
            <Input
              label="Minimum Peer Reviewers"
              type="number"
              defaultValue="3"
              min="1"
              max="10"
            />

            <Input
              label="Maximum Peer Reviewers"
              type="number"
              defaultValue="5"
              min="1"
              max="10"
            />
          </div>
        </div>
      </Card>

      {/* Notification Settings */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Notification Settings</h2>
        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Email Notifications</div>
              <div className="text-sm text-gray-600">Send email reminders for pending tasks</div>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Deadline Reminders</div>
              <div className="text-sm text-gray-600">Remind users 3 days before deadlines</div>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Manager Notifications</div>
              <div className="text-sm text-gray-600">Notify managers when team members complete tasks</div>
            </div>
          </label>
        </div>
      </Card>

      {/* AI Settings */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">AI Configuration</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <Select
            label="AI Model"
            defaultValue="claude-sonnet"
            options={[
              { value: 'claude-sonnet', label: 'Claude Sonnet (Recommended)' },
              { value: 'claude-opus', label: 'Claude Opus (Advanced)' },
              { value: 'claude-haiku', label: 'Claude Haiku (Fast)' },
            ]}
          />

          <Select
            label="Draft Generation Mode"
            defaultValue="balanced"
            options={[
              { value: 'detailed', label: 'Detailed Analysis' },
              { value: 'balanced', label: 'Balanced' },
              { value: 'concise', label: 'Concise' },
            ]}
          />

          <div className="md:col-span-2">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <div>
                <div className="font-medium">Include Clarifying Questions</div>
                <div className="text-sm text-gray-600">
                  AI will generate questions to help managers provide better evaluations
                </div>
              </div>
            </label>
          </div>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex gap-3 justify-end">
        <Button variant="outline">
          Reset to Defaults
        </Button>
        <Button
          variant="primary"
          onClick={handleSave}
          isLoading={isSaving}
        >
          Save Settings
        </Button>
      </div>
    </div>
  );
}
