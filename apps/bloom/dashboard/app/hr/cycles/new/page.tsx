'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import PageHeader from '@/components/PageHeader';
import Card from '@/components/Card';
import Input from '@/components/Input';
import Select from '@/components/Select';
import Button from '@/components/Button';
import AlertBanner from '@/components/AlertBanner';

interface CycleForm {
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  peer_selection_deadline: string;
  self_eval_deadline: string;
  manager_review_deadline: string;
  template_id: string;
  participant_groups: string[];
}

export default function NewCyclePage() {
  const router = useRouter();
  const [formData, setFormData] = useState<CycleForm>({
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    peer_selection_deadline: '',
    self_eval_deadline: '',
    manager_review_deadline: '',
    template_id: '',
    participant_groups: [],
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/hr/cycles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to create cycle');

      const data = await response.json();
      router.push(`/hr/cycles/${data.id}`);
    } catch (error) {
      setError('Failed to create evaluation cycle. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create New Evaluation Cycle"
        description="Set up a new performance evaluation cycle"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'HR Dashboard', href: '/hr' },
          { label: 'Cycles', href: '/hr/cycles' },
          { label: 'New Cycle', href: '/hr/cycles/new' },
        ]}
      />

      {error && <AlertBanner alerts={[{
        id: 'new-cycle-error',
        type: 'error',
        title: 'Error',
        message: error
      }]} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6">Basic Information</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <Input
                label="Cycle Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Q4 2024 Performance Review"
                required
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe the purpose and scope of this evaluation cycle..."
                className="w-full min-h-[100px] p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <Input
              label="Start Date"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              required
            />

            <Input
              label="End Date"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
              required
            />
          </div>
        </Card>

        {/* Deadlines */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6">Phase Deadlines</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Input
              label="Peer Selection Deadline"
              type="date"
              value={formData.peer_selection_deadline}
              onChange={(e) => setFormData({ ...formData, peer_selection_deadline: e.target.value })}
              required
            />

            <Input
              label="Self-Evaluation Deadline"
              type="date"
              value={formData.self_eval_deadline}
              onChange={(e) => setFormData({ ...formData, self_eval_deadline: e.target.value })}
              required
            />

            <Input
              label="Manager Review Deadline"
              type="date"
              value={formData.manager_review_deadline}
              onChange={(e) => setFormData({ ...formData, manager_review_deadline: e.target.value })}
              required
            />
          </div>
        </Card>

        {/* Configuration */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6">Configuration</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <Select
              label="Evaluation Template"
              value={formData.template_id}
              onChange={(value) => setFormData({ ...formData, template_id: String(value) })}
              options={[
                { value: '', label: 'Select a template' },
                { value: 'standard', label: 'Standard Performance Review' },
                { value: 'leadership', label: 'Leadership Assessment' },
                { value: 'technical', label: 'Technical Skills Evaluation' },
              ]}
              required
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Participant Groups
              </label>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.participant_groups.includes('all_employees')}
                    onChange={(e) => {
                      const groups = e.target.checked
                        ? [...formData.participant_groups, 'all_employees']
                        : formData.participant_groups.filter(g => g !== 'all_employees');
                      setFormData({ ...formData, participant_groups: groups });
                    }}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm">All Employees</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.participant_groups.includes('managers_only')}
                    onChange={(e) => {
                      const groups = e.target.checked
                        ? [...formData.participant_groups, 'managers_only']
                        : formData.participant_groups.filter(g => g !== 'managers_only');
                      setFormData({ ...formData, participant_groups: groups });
                    }}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm">Managers Only</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.participant_groups.includes('custom_group')}
                    onChange={(e) => {
                      const groups = e.target.checked
                        ? [...formData.participant_groups, 'custom_group']
                        : formData.participant_groups.filter(g => g !== 'custom_group');
                      setFormData({ ...formData, participant_groups: groups });
                    }}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm">Custom Group</span>
                </label>
              </div>
            </div>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <Button
            type="button"
            variant="ghost"
            onClick={() => router.push('/hr/cycles')}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
          >
            Create Cycle
          </Button>
        </div>
      </form>

      {/* Guidelines */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-3">Cycle Creation Guidelines</h3>
        <ul className="text-sm text-blue-800 space-y-2 list-disc list-inside">
          <li>Ensure deadlines allow sufficient time for each phase</li>
          <li>Peer selection should be completed before self-evaluations</li>
          <li>Manager reviews should follow self-evaluations and peer feedback</li>
          <li>Allow 2-3 weeks for each major phase</li>
          <li>Consider holidays and company events when setting dates</li>
          <li>Communicate the cycle timeline to all participants in advance</li>
        </ul>
      </Card>
    </div>
  );
}
