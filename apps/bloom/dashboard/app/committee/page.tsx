'use client';

import { useEffect, useState } from 'react';
import { CheckCircle } from 'lucide-react';
import PageHeader from '@/components/PageHeader';
import MetricsGrid from '@/components/MetricsGrid';
import Card from '@/components/Card';
import Badge from '@/components/Badge';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';
import Link from 'next/link';

interface CommitteeItem {
  id: string;
  employee_name: string;
  manager_name: string;
  cycle_name: string;
  manager_rating: number;
  calibration_status: 'pending' | 'in_progress' | 'completed';
  priority: 'high' | 'medium' | 'low';
  requires_discussion: boolean;
}

export default function CommitteeDashboardPage() {
  const [items, setItems] = useState<CommitteeItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        const response = await fetch('/api/committee/queue');
        const data = await response.json();
        setItems(data);
      } catch (error) {
        console.error('Failed to fetch committee items:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchItems();
  }, []);

  const pendingReviews = items.filter(i => i.calibration_status === 'pending');
  const inProgress = items.filter(i => i.calibration_status === 'in_progress');
  const highPriority = items.filter(i => i.priority === 'high');

  return (
    <div className="space-y-6">
      <PageHeader
        title="Committee Dashboard"
        description="Review and calibrate performance evaluations"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Committee', href: '/committee' },
        ]}
      />

      {/* Metrics Overview */}
      <MetricsGrid metrics={[]} />

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="xl" />
        </div>
      ) : (
        <>
          {/* High Priority Reviews */}
          {highPriority.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                High Priority Reviews
                <Badge variant="red">{highPriority.length}</Badge>
              </h2>

              <div className="grid md:grid-cols-2 gap-4">
                {highPriority.map((item) => (
                  <Link key={item.id} href={`/committee/calibration/${item.id}`}>
                    <Card className="p-6 border-l-4 border-red-500 hover:shadow-lg transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="text-lg font-semibold">{item.employee_name}</h3>
                          <p className="text-sm text-gray-600">{item.manager_name} • {item.cycle_name}</p>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <Badge variant="red">High Priority</Badge>
                          <div className="text-2xl font-bold text-blue-600">
                            {item.manager_rating.toFixed(1)}
                          </div>
                        </div>
                      </div>
                      {item.requires_discussion && (
                        <Badge variant="purple">Requires Discussion</Badge>
                      )}
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Pending Reviews */}
          <div>
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              Pending Reviews
              {pendingReviews.length > 0 && (
                <Badge variant="purple">{pendingReviews.length}</Badge>
              )}
            </h2>

            {pendingReviews.length === 0 ? (
              <EmptyState
                title="No pending reviews"
                description="All evaluations have been reviewed."
                icon={CheckCircle}
              />
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {pendingReviews.map((item) => (
                  <Link key={item.id} href={`/committee/calibration/${item.id}`}>
                    <Card className="p-6 hover:shadow-lg transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="text-lg font-semibold">{item.employee_name}</h3>
                          <p className="text-sm text-gray-600">{item.manager_name} • {item.cycle_name}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-600">Manager Rating</div>
                          <div className="text-2xl font-bold text-blue-600">
                            {item.manager_rating.toFixed(1)}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Badge variant={
                          item.priority === 'high' ? 'red' :
                          item.priority === 'medium' ? 'yellow' :
                          'gray'
                        }>
                          {item.priority} priority
                        </Badge>
                        {item.requires_discussion && (
                          <Badge variant="blue">Discussion needed</Badge>
                        )}
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* In Progress */}
          {inProgress.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                In Progress
                <Badge variant="blue">{inProgress.length}</Badge>
              </h2>

              <div className="grid md:grid-cols-3 gap-4">
                {inProgress.map((item) => (
                  <Link key={item.id} href={`/committee/calibration/${item.id}`}>
                    <Card className="p-4 hover:shadow-lg transition-shadow">
                      <h3 className="font-semibold mb-1">{item.employee_name}</h3>
                      <p className="text-sm text-gray-600 mb-2">{item.cycle_name}</p>
                      <Badge variant="blue">In Review</Badge>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid md:grid-cols-3 gap-4">
            <Link href="/committee/calibration">
              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
                <div className="text-center">
                  <div className="text-3xl mb-3">⚖️</div>
                  <h3 className="font-semibold mb-2">Calibration Session</h3>
                  <p className="text-sm text-gray-600">Start group calibration</p>
                </div>
              </Card>
            </Link>

            <Link href="/committee/reviews">
              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
                <div className="text-center">
                  <div className="text-3xl mb-3">📋</div>
                  <h3 className="font-semibold mb-2">All Reviews</h3>
                  <p className="text-sm text-gray-600">View all committee items</p>
                </div>
              </Card>
            </Link>

            <Link href="/help">
              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
                <div className="text-center">
                  <div className="text-3xl mb-3">📚</div>
                  <h3 className="font-semibold mb-2">Guidelines</h3>
                  <p className="text-sm text-gray-600">Calibration best practices</p>
                </div>
              </Card>
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
