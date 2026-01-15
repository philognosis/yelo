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

interface ManagerEvaluation {
  id: string;
  employee_name: string;
  employee_role: string;
  cycle_name: string;
  status: string;
  due_date: string;
  ai_draft_ready: boolean;
  has_manager_draft: boolean;
  self_eval_completed: boolean;
  peer_feedback_count: number;
  timeline: any[];
}

export default function ManagerEvaluationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [evaluation, setEvaluation] = useState<ManagerEvaluation | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchEvaluation = async () => {
      try {
        const response = await fetch(`/api/manager/evaluations/${params.id}`);
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
        <Button onClick={() => router.push('/manager')} className="mt-4">
          Back to Team Evaluations
        </Button>
      </div>
    );
  }

  const canViewDraft = evaluation.ai_draft_ready;
  const canEdit = evaluation.status === 'manager_review';
  const isComplete = evaluation.status === 'completed';

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Evaluation: ${evaluation.employee_name}`}
        description={`${evaluation.employee_role} • ${evaluation.cycle_name}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Team Evaluations', href: '/manager' },
          { label: evaluation.employee_name, href: `/manager/evaluations/${params.id}` },
        ]}
      />

      {/* Status Banner */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-2">Evaluation Status</h2>
            <StateIndicator state={evaluation.status} />
            {evaluation.ai_draft_ready && (
              <Badge variant="info" className="mt-2">AI Draft Available</Badge>
            )}
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
            <h2 className="text-xl font-semibold mb-4">Manager Actions</h2>
            <div className="space-y-3">
              {/* View AI Draft */}
              {canViewDraft && (
                <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="info">AI</Badge>
                    <div>
                      <div className="font-medium">Review AI-Generated Draft</div>
                      <div className="text-sm text-gray-600">
                        AI has analyzed all available feedback and created a draft evaluation
                      </div>
                    </div>
                  </div>
                  <Link href={`/manager/evaluations/${params.id}/draft`}>
                    <Button variant="primary">View Draft</Button>
                  </Link>
                </div>
              )}

              {/* Edit Evaluation */}
              {canEdit && (
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant={evaluation.has_manager_draft ? 'success' : 'warning'}>
                      {evaluation.has_manager_draft ? 'In Progress' : 'Not Started'}
                    </Badge>
                    <div>
                      <div className="font-medium">
                        {evaluation.has_manager_draft ? 'Continue Editing' : 'Start Evaluation'}
                      </div>
                      <div className="text-sm text-gray-600">
                        {evaluation.has_manager_draft
                          ? 'Review and finalize your evaluation'
                          : 'Create your evaluation from scratch or use AI draft'
                        }
                      </div>
                    </div>
                  </div>
                  <Link href={`/manager/evaluations/${params.id}/edit`}>
                    <Button variant="primary">
                      {evaluation.has_manager_draft ? 'Edit' : 'Start'}
                    </Button>
                  </Link>
                </div>
              )}

              {/* Submit Evaluation */}
              {evaluation.has_manager_draft && (
                <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="success">Ready</Badge>
                    <div>
                      <div className="font-medium">Submit for Review</div>
                      <div className="text-sm text-gray-600">
                        Finalize and submit your evaluation
                      </div>
                    </div>
                  </div>
                  <Link href={`/manager/evaluations/${params.id}/submit`}>
                    <Button variant="success">Submit</Button>
                  </Link>
                </div>
              )}

              {/* View Completed */}
              {isComplete && (
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="success">✓ Complete</Badge>
                    <div>
                      <div className="font-medium">Evaluation Completed</div>
                      <div className="text-sm text-gray-600">
                        View the final evaluation and feedback
                      </div>
                    </div>
                  </div>
                  <Button variant="outline">View Final</Button>
                </div>
              )}
            </div>
          </Card>

          {/* Available Data */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Available Information</h2>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {evaluation.self_eval_completed ? '✓' : '—'}
                </div>
                <div className="text-sm font-medium mt-2">Self-Evaluation</div>
                <div className="text-xs text-gray-600 mt-1">
                  {evaluation.self_eval_completed ? 'Completed' : 'Not yet submitted'}
                </div>
              </div>

              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {evaluation.peer_feedback_count}
                </div>
                <div className="text-sm font-medium mt-2">Peer Reviews</div>
                <div className="text-xs text-gray-600 mt-1">
                  Feedback received
                </div>
              </div>

              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {evaluation.ai_draft_ready ? '✓' : '⏳'}
                </div>
                <div className="text-sm font-medium mt-2">AI Analysis</div>
                <div className="text-xs text-gray-600 mt-1">
                  {evaluation.ai_draft_ready ? 'Draft ready' : 'Processing'}
                </div>
              </div>
            </div>
          </Card>

          {/* Evaluation Details */}
          <EvaluationDetail evaluationId={params.id as string} role="manager" />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Employee Info */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Employee Info</h2>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-600">Name</div>
                <div className="font-medium">{evaluation.employee_name}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Role</div>
                <div className="font-medium">{evaluation.employee_role}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Cycle</div>
                <div className="font-medium">{evaluation.cycle_name}</div>
              </div>
            </div>
          </Card>

          {/* Timeline */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Timeline</h2>
            <EvaluationTimeline events={evaluation.timeline} />
          </Card>

          {/* Resources */}
          <Card className="p-6 bg-blue-50 border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-3">Manager Resources</h3>
            <div className="space-y-2">
              <Link href="/help" className="block text-sm text-blue-700 hover:underline">
                → Evaluation guidelines
              </Link>
              <Link href="/help" className="block text-sm text-blue-700 hover:underline">
                → Effective feedback tips
              </Link>
              <Link href="/help" className="block text-sm text-blue-700 hover:underline">
                → Rating calibration guide
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
