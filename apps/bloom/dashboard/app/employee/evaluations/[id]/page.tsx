'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PageHeader } from '../../../../components/PageHeader';
import { EvaluationDetail } from '../../../../components/EvaluationDetail';
import { EvaluationTimeline } from '../../../../components/EvaluationTimeline';
import { StateIndicator } from '../../../../components/StateIndicator';
import { Button } from '../../../../components/Button';
import { Card } from '../../../../components/Card';
import { Badge } from '../../../../components/Badge';
import { LoadingSpinner } from '../../../../components/LoadingSpinner';
import Link from 'next/link';

interface EvaluationData {
  id: string;
  employee_name: string;
  cycle_name: string;
  status: string;
  due_date: string;
  progress: {
    peer_selection: boolean;
    self_eval: boolean;
    manager_review: boolean;
  };
  timeline: any[];
}

export default function EmployeeEvaluationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [evaluation, setEvaluation] = useState<EvaluationData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchEvaluation = async () => {
      try {
        const response = await fetch(`/api/employee/evaluations/${params.id}`);
        const data = await response.json();
        setEvaluation(data);
      } catch (error) {
        console.error('Failed to fetch evaluation:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvaluation();
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">Evaluation not found</h2>
        <Button onClick={() => router.push('/employee')} className="mt-4">
          Back to Evaluations
        </Button>
      </div>
    );
  }

  const canSelectPeers = evaluation.status === 'peer_selection' && !evaluation.progress.peer_selection;
  const canSelfEval = ['peer_selection', 'self_evaluation'].includes(evaluation.status) && !evaluation.progress.self_eval;
  const canViewFeedback = ['completed', 'finalized'].includes(evaluation.status);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Evaluation: ${evaluation.cycle_name}`}
        description="View and complete your evaluation tasks"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'My Evaluations', href: '/employee' },
          { label: evaluation.cycle_name, href: `/employee/evaluations/${params.id}` },
        ]}
      />

      {/* Status Banner */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-2">Evaluation Status</h2>
            <StateIndicator state={evaluation.status} />
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">Due Date</div>
            <div className="text-lg font-semibold">
              {new Date(evaluation.due_date).toLocaleDateString()}
            </div>
          </div>
        </div>
      </Card>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Action Items */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Action Items</h2>
            <div className="space-y-3">
              {/* Peer Selection */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {evaluation.progress.peer_selection ? (
                    <Badge variant="success">✓ Complete</Badge>
                  ) : (
                    <Badge variant="warning">Pending</Badge>
                  )}
                  <div>
                    <div className="font-medium">Select Peer Reviewers</div>
                    <div className="text-sm text-gray-600">Choose colleagues to provide feedback</div>
                  </div>
                </div>
                {canSelectPeers && (
                  <Link href={`/employee/evaluations/${params.id}/peer-selection`}>
                    <Button variant="primary">Select Peers</Button>
                  </Link>
                )}
              </div>

              {/* Self Evaluation */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {evaluation.progress.self_eval ? (
                    <Badge variant="success">✓ Complete</Badge>
                  ) : (
                    <Badge variant="warning">Pending</Badge>
                  )}
                  <div>
                    <div className="font-medium">Complete Self-Evaluation</div>
                    <div className="text-sm text-gray-600">Evaluate your own performance</div>
                  </div>
                </div>
                {canSelfEval && (
                  <Link href={`/employee/evaluations/${params.id}/self-eval`}>
                    <Button variant="primary">
                      {evaluation.progress.self_eval ? 'View' : 'Start'}
                    </Button>
                  </Link>
                )}
              </div>

              {/* View Feedback */}
              {canViewFeedback && (
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="success">✓ Available</Badge>
                    <div>
                      <div className="font-medium">View Final Feedback</div>
                      <div className="text-sm text-gray-600">Review your completed evaluation</div>
                    </div>
                  </div>
                  <Link href={`/employee/evaluations/${params.id}/feedback`}>
                    <Button variant="primary">View Feedback</Button>
                  </Link>
                </div>
              )}
            </div>
          </Card>

          {/* Evaluation Details */}
          <EvaluationDetail evaluationId={params.id as string} role="employee" />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Timeline */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Timeline</h2>
            <EvaluationTimeline events={evaluation.timeline} />
          </Card>

          {/* Progress */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Progress</h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm">Peer Selection</span>
                <Badge variant={evaluation.progress.peer_selection ? 'success' : 'default'}>
                  {evaluation.progress.peer_selection ? 'Done' : 'Pending'}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Self-Evaluation</span>
                <Badge variant={evaluation.progress.self_eval ? 'success' : 'default'}>
                  {evaluation.progress.self_eval ? 'Done' : 'Pending'}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Manager Review</span>
                <Badge variant={evaluation.progress.manager_review ? 'success' : 'default'}>
                  {evaluation.progress.manager_review ? 'Done' : 'In Progress'}
                </Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
