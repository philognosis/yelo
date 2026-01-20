'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import PageHeader from '@/components/PageHeader';
import Card from '@/components/Card';
import Badge from '@/components/Badge';
import Button from '@/components/Button';
import LoadingSpinner from '@/components/LoadingSpinner';
import EvaluationChart from '@/components/EvaluationChart';
import ActivityFeed from '@/components/ActivityFeed';

interface CycleDetail {
  id: string;
  name: string;
  description: string;
  status: string;
  start_date: string;
  end_date: string;
  deadlines: {
    peer_selection: string;
    self_eval: string;
    manager_review: string;
  };
  statistics: {
    total_participants: number;
    completed: number;
    in_progress: number;
    not_started: number;
    completion_rate: number;
    avg_rating: number;
  };
  recent_activity: any[];
}

export default function CycleDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [cycle, setCycle] = useState<CycleDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCycle = async () => {
      try {
        const response = await fetch(`/api/hr/cycles/${params?.id || ""}`);
        const data = await response.json();
        setCycle(data);
      } catch (error) {
        console.error('Failed to fetch cycle:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCycle();
  }, [params?.id]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  if (!cycle) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">Cycle not found</h2>
        <Button onClick={() => router.push('/hr/cycles')} className="mt-4">
          Back to Cycles
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={cycle.name}
        description={cycle.description}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'HR Dashboard', href: '/hr' },
          { label: 'Cycles', href: '/hr/cycles' },
          { label: cycle.name, href: `/hr/cycles/${params?.id || ""}` },
        ]}
        actions={
          <div className="flex gap-3">
            <Button variant="ghost">Edit Cycle</Button>
            <Button variant="secondary">Export Data</Button>
          </div>
        }
      />

      {/* Status Banner */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-2">Cycle Status</h2>
            <Badge variant="blue" className="text-lg px-4 py-2">
              {cycle.status.toUpperCase()}
            </Badge>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">Completion Rate</div>
            <div className="text-4xl font-bold text-blue-600">
              {cycle.statistics.completion_rate}%
            </div>
          </div>
        </div>
      </Card>

      {/* Statistics */}
      <div className="grid md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Total Participants</div>
          <div className="text-3xl font-bold text-blue-600">
            {cycle.statistics.total_participants}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Completed</div>
          <div className="text-3xl font-bold text-green-600">
            {cycle.statistics.completed}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">In Progress</div>
          <div className="text-3xl font-bold text-orange-600">
            {cycle.statistics.in_progress}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Not Started</div>
          <div className="text-3xl font-bold text-gray-600">
            {cycle.statistics.not_started}
          </div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Timeline */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6">Cycle Timeline</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">Cycle Start</div>
                  <div className="text-sm text-gray-600">Evaluation period begins</div>
                </div>
                <div className="text-right">
                  <div className="font-medium">
                    {new Date(cycle.start_date).toLocaleDateString()}
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">Peer Selection Deadline</div>
                  <div className="text-sm text-gray-600">Employees select peer reviewers</div>
                </div>
                <div className="text-right">
                  <div className="font-medium">
                    {new Date(cycle.deadlines.peer_selection).toLocaleDateString()}
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">Self-Evaluation Deadline</div>
                  <div className="text-sm text-gray-600">Employees complete self-assessments</div>
                </div>
                <div className="text-right">
                  <div className="font-medium">
                    {new Date(cycle.deadlines.self_eval).toLocaleDateString()}
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">Manager Review Deadline</div>
                  <div className="text-sm text-gray-600">Managers submit evaluations</div>
                </div>
                <div className="text-right">
                  <div className="font-medium">
                    {new Date(cycle.deadlines.manager_review).toLocaleDateString()}
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">Cycle End</div>
                  <div className="text-sm text-gray-600">Evaluation period ends</div>
                </div>
                <div className="text-right">
                  <div className="font-medium">
                    {new Date(cycle.end_date).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Recent Activity */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
            <ActivityFeed activities={[]} />
          </Card>

          {/* Performance Distribution */}
          {cycle.statistics.avg_rating > 0 && (
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">Performance Distribution</h2>
              <EvaluationChart
                type="bar"
                data={[3.8, 4.2, 3.9, 4.5, 4.1].map((value, index) => ({
                  name: `Rating ${index + 1}`,
                  value: value
                }))}
              />
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Actions</h2>
            <div className="space-y-3">
              <Button variant="primary" className="w-full">
                Send Reminder
              </Button>
              <Button variant="secondary" className="w-full">
                Download Report
              </Button>
              <Button variant="ghost" className="w-full">
                View All Evaluations
              </Button>
            </div>
          </Card>

          {/* Cycle Info */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Cycle Information</h2>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-600">Average Rating</div>
                <div className="text-2xl font-bold text-blue-600">
                  {cycle.statistics.avg_rating > 0
                    ? cycle.statistics.avg_rating.toFixed(1)
                    : '—'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Duration</div>
                <div className="font-medium">
                  {Math.ceil(
                    (new Date(cycle.end_date).getTime() - new Date(cycle.start_date).getTime()) /
                    (1000 * 60 * 60 * 24)
                  )} days
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
