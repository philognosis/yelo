'use client';

import { useEffect, useState } from 'react';
import PageHeader from '@/components/PageHeader';
import EvaluationCard from '@/components/EvaluationCard';
import MetricsGrid from '@/components/MetricsGrid';
import Card from '@/components/Card';
import Badge from '@/components/Badge';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';
import AlertBanner from '@/components/AlertBanner';
import Link from 'next/link';

interface TeamEvaluation {
  id: string;
  employee_name: string;
  cycle_name: string;
  status: string;
  due_date: string;
  ai_draft_ready: boolean;
  requires_attention: boolean;
}

export default function ManagerDashboardPage() {
  const [evaluations, setEvaluations] = useState<TeamEvaluation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchEvaluations = async () => {
      try {
        const response = await fetch('/api/manager/team-evaluations');
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

  const pendingReviews = evaluations.filter(e =>
    e.status === 'manager_review' && !e.ai_draft_ready
  );
  const draftsReady = evaluations.filter(e => e.ai_draft_ready);
  const completed = evaluations.filter(e => e.status === 'completed');
  const requiresAttention = evaluations.filter(e => e.requires_attention);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team Evaluations"
        description="Manage performance evaluations for your direct reports"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Team Evaluations', href: '/manager' },
        ]}
      />

      {/* Metrics Overview */}
      <MetricsGrid metrics={[]} />

      {/* Alerts */}
      {requiresAttention.length > 0 && (
        <AlertBanner
          type="warning"
          message={`${requiresAttention.length} evaluation(s) require your attention`}
        />
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="xl" />
        </div>
      ) : (
        <>
          {/* AI Drafts Ready */}
          {draftsReady.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                AI Drafts Ready for Review
                <Badge variant="blue">{draftsReady.length}</Badge>
              </h2>

              <div className="grid md:grid-cols-2 gap-4">
                {draftsReady.map((evaluation) => (
                  <Link key={evaluation.id} href={`/manager/evaluations/${evaluation.id}/draft`}>
                    <EvaluationCard
                      evaluation={evaluation}
                      showAIBadge
                    />
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
                description="All your team evaluations are up to date."
                icon="✓"
              />
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {pendingReviews.map((evaluation) => (
                  <Link key={evaluation.id} href={`/manager/evaluations/${evaluation.id}`}>
                    <EvaluationCard evaluation={evaluation} />
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Completed Reviews */}
          {completed.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                Completed Reviews
                <Badge variant="blue">{completed.length}</Badge>
              </h2>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {completed.map((evaluation) => (
                  <Link key={evaluation.id} href={`/manager/evaluations/${evaluation.id}`}>
                    <EvaluationCard evaluation={evaluation} compact />
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid md:grid-cols-3 gap-4">
            <Link href="/manager/team">
              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
                <div className="text-center">
                  <div className="text-3xl mb-3">👥</div>
                  <h3 className="font-semibold mb-2">Team Overview</h3>
                  <p className="text-sm text-gray-600">View team metrics and insights</p>
                </div>
              </Card>
            </Link>

            <Link href="/notifications">
              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
                <div className="text-center">
                  <div className="text-3xl mb-3">🔔</div>
                  <h3 className="font-semibold mb-2">Notifications</h3>
                  <p className="text-sm text-gray-600">Check important updates</p>
                </div>
              </Card>
            </Link>

            <Link href="/help">
              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
                <div className="text-center">
                  <div className="text-3xl mb-3">❓</div>
                  <h3 className="font-semibold mb-2">Help & Resources</h3>
                  <p className="text-sm text-gray-600">Get manager guidelines</p>
                </div>
              </Card>
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
