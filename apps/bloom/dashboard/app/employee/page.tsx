'use client';

import { useEffect, useState } from 'react';
import PageHeader from '@/components/PageHeader';
import EvaluationCard from '@/components/EvaluationCard';
import MetricsGrid from '@/components/MetricsGrid';
import Card from '@/components/Card';
import Badge from '@/components/Badge';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';
import Link from 'next/link';

interface Evaluation {
  id: string;
  cycle_name: string;
  status: string;
  due_date: string;
  progress: {
    self_eval: boolean;
    peer_selection: boolean;
    manager_review: boolean;
  };
}

export default function EmployeeDashboardPage() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch employee's evaluations
    const fetchEvaluations = async () => {
      try {
        const response = await fetch('/api/employee/evaluations');
        const data = await response.json();
        setEvaluations(data);
      } catch (error) {
        console.error('Failed to fetch evaluations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvaluations();
  }, []);

  const activeEvaluations = evaluations.filter(e =>
    ['peer_selection', 'self_evaluation', 'manager_review', 'committee_review'].includes(e.status)
  );
  const completedEvaluations = evaluations.filter(e => e.status === 'completed');

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Evaluations"
        description="Track and complete your performance evaluations"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'My Evaluations', href: '/employee' },
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
          {/* Active Evaluations */}
          <div>
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              Active Evaluations
              {activeEvaluations.length > 0 && (
                <Badge variant="blue">{activeEvaluations.length}</Badge>
              )}
            </h2>

            {activeEvaluations.length === 0 ? (
              <EmptyState
                title="No active evaluations"
                description="You don't have any evaluations in progress right now."
              />
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {activeEvaluations.map((evaluation) => (
                  <Link key={evaluation.id} href={`/employee/evaluations/${evaluation.id}`}>
                    <EvaluationCard
                      id={evaluation.id}
                      title={evaluation.cycle_name}
                      period={evaluation.cycle_name}
                      dueDate={new Date(evaluation.due_date).toLocaleDateString()}
                      status={evaluation.status === 'completed' ? 'completed' :
                              evaluation.status === 'not_started' ? 'not_started' :
                              'in_progress'}
                      currentPhase={evaluation.status}
                    />
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Completed Evaluations */}
          {completedEvaluations.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                Completed Evaluations
                <Badge variant="blue">{completedEvaluations.length}</Badge>
              </h2>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {completedEvaluations.map((evaluation) => (
                  <Link key={evaluation.id} href={`/employee/evaluations/${evaluation.id}`}>
                    <EvaluationCard
                      id={evaluation.id}
                      title={evaluation.cycle_name}
                      period={evaluation.cycle_name}
                      dueDate={new Date(evaluation.due_date).toLocaleDateString()}
                      status="completed"
                      currentPhase={evaluation.status}
                    />
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
            <div className="grid md:grid-cols-3 gap-4">
              <Link href="/employee/profile">
                <div className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
                  <div className="text-2xl mb-2">👤</div>
                  <div className="font-medium">My Profile</div>
                  <div className="text-sm text-gray-600 mt-1">Update your information</div>
                </div>
              </Link>
              <Link href="/notifications">
                <div className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
                  <div className="text-2xl mb-2">🔔</div>
                  <div className="font-medium">Notifications</div>
                  <div className="text-sm text-gray-600 mt-1">View your updates</div>
                </div>
              </Link>
              <Link href="/help">
                <div className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
                  <div className="text-2xl mb-2">❓</div>
                  <div className="font-medium">Help & Support</div>
                  <div className="text-sm text-gray-600 mt-1">Get assistance</div>
                </div>
              </Link>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
