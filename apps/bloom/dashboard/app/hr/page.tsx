'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '../../components/PageHeader';
import { MetricsGrid } from '../../components/MetricsGrid';
import { Card } from '../../components/Card';
import { Badge } from '../../components/Badge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ActivityFeed } from '../../components/ActivityFeed';
import { EvaluationChart } from '../../components/EvaluationChart';
import { AlertBanner } from '../../components/AlertBanner';
import Link from 'next/link';

interface SystemMetrics {
  total_employees: number;
  active_cycles: number;
  pending_evaluations: number;
  completion_rate: number;
  avg_rating: number;
  alerts: Array<{
    type: string;
    message: string;
    count: number;
  }>;
}

export default function HRDashboardPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/hr/dashboard');
        const data = await response.json();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="HR Dashboard"
        description="Organization-wide performance evaluation overview"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'HR Dashboard', href: '/hr' },
        ]}
      />

      {/* System Alerts */}
      {metrics?.alerts && metrics.alerts.length > 0 && (
        <div className="space-y-3">
          {metrics.alerts.map((alert, idx) => (
            <AlertBanner
              key={idx}
              type={alert.type as any}
              message={`${alert.message} (${alert.count})`}
            />
          ))}
        </div>
      )}

      {/* Metrics Overview */}
      <MetricsGrid role="hr_admin" />

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick Stats */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Evaluation Progress</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Completion Rate</span>
                  <span className="text-2xl font-bold text-green-600">
                    {metrics?.completion_rate || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${metrics?.completion_rate || 0}%` }}
                  />
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Average Rating</h3>
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-600">
                  {metrics?.avg_rating?.toFixed(1) || '—'}
                </div>
                <div className="text-sm text-gray-600 mt-2">out of 5.0</div>
              </div>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
            <ActivityFeed />
          </Card>

          {/* Performance Distribution */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Performance Distribution</h2>
            <EvaluationChart data={[4.2, 3.8, 4.5, 3.9, 4.1, 4.3, 3.7, 4.0]} />
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link href="/hr/cycles/new" className="block">
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-all">
                  <div className="font-medium text-blue-900">Create New Cycle</div>
                  <div className="text-sm text-blue-700">Start a new evaluation cycle</div>
                </div>
              </Link>

              <Link href="/hr/evaluations" className="block">
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-all">
                  <div className="font-medium text-purple-900">View All Evaluations</div>
                  <div className="text-sm text-purple-700">Monitor all evaluations</div>
                </div>
              </Link>

              <Link href="/hr/analytics" className="block">
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-all">
                  <div className="font-medium text-green-900">Analytics & Reports</div>
                  <div className="text-sm text-green-700">View detailed insights</div>
                </div>
              </Link>

              <Link href="/hr/settings" className="block">
                <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-all">
                  <div className="font-medium text-gray-900">System Settings</div>
                  <div className="text-sm text-gray-700">Configure the system</div>
                </div>
              </Link>
            </div>
          </Card>

          {/* Active Cycles */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              Active Cycles
              {metrics?.active_cycles ? (
                <Badge variant="info">{metrics.active_cycles}</Badge>
              ) : null}
            </h2>
            <Link href="/hr/cycles">
              <div className="text-sm text-blue-600 hover:underline">
                Manage all cycles →
              </div>
            </Link>
          </Card>

          {/* System Health */}
          <Card className="p-6 bg-green-50 border-green-200">
            <h3 className="font-semibold text-green-900 mb-3">System Health</h3>
            <div className="space-y-2 text-sm text-green-800">
              <div className="flex justify-between">
                <span>API Status</span>
                <Badge variant="success">Healthy</Badge>
              </div>
              <div className="flex justify-between">
                <span>AI Services</span>
                <Badge variant="success">Active</Badge>
              </div>
              <div className="flex justify-between">
                <span>Notifications</span>
                <Badge variant="success">Running</Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
