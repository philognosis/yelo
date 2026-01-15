'use client';

import { useAuth } from '../../contexts/AuthContext';
import { PageHeader } from '../../components/PageHeader';
import { MetricsGrid } from '../../components/MetricsGrid';
import { ActivityFeed } from '../../components/ActivityFeed';
import { AlertBanner } from '../../components/AlertBanner';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import Link from 'next/link';

/**
 * Main dashboard with role-based view
 * Shows different content based on user role
 */
export default function DashboardPage() {
  const { user } = useAuth();

  if (!user) return null;

  const roleSpecificContent = {
    employee: {
      title: 'My Dashboard',
      description: 'Track your evaluations and career development',
      cta: { label: 'View My Evaluations', href: '/employee' },
    },
    manager: {
      title: 'Team Dashboard',
      description: 'Manage your team\'s performance evaluations',
      cta: { label: 'View Team Evaluations', href: '/manager' },
    },
    hr_admin: {
      title: 'HR Dashboard',
      description: 'Oversee organization-wide evaluation cycles',
      cta: { label: 'Manage Cycles', href: '/hr/cycles' },
    },
    committee: {
      title: 'Committee Dashboard',
      description: 'Review and calibrate performance evaluations',
      cta: { label: 'View Calibration Queue', href: '/committee/calibration' },
    },
  };

  const content = roleSpecificContent[user.role as keyof typeof roleSpecificContent] || roleSpecificContent.employee;

  return (
    <div className="space-y-6">
      <PageHeader
        title={content.title}
        description={content.description}
      />

      {/* Role-specific alerts */}
      <AlertBanner
        type="info"
        message="Welcome to Bloom! This is your personalized dashboard."
      />

      {/* Metrics Overview */}
      <MetricsGrid role={user.role} />

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2">
          <Card>
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
              <ActivityFeed />
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <Card>
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
              <div className="space-y-3">
                <Link href={content.cta.href} className="block">
                  <Button variant="primary" fullWidth>
                    {content.cta.label}
                  </Button>
                </Link>
                <Link href="/notifications" className="block">
                  <Button variant="secondary" fullWidth>
                    View Notifications
                  </Button>
                </Link>
                <Link href="/help" className="block">
                  <Button variant="outline" fullWidth>
                    Get Help
                  </Button>
                </Link>
              </div>
            </div>
          </Card>

          {/* User Info */}
          <Card className="mt-6">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Your Profile</h2>
              <div className="space-y-2">
                <div>
                  <span className="text-sm text-gray-600">Name</span>
                  <p className="font-medium">{user.name}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Email</span>
                  <p className="font-medium">{user.email}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Role</span>
                  <p className="font-medium capitalize">{user.role.replace('_', ' ')}</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
