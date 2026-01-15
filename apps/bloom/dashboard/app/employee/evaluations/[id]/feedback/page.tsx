'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PageHeader } from '../../../../../components/PageHeader';
import { Card } from '../../../../../components/Card';
import { Badge } from '../../../../../components/Badge';
import { Button } from '../../../../../components/Button';
import { LoadingSpinner } from '../../../../../components/LoadingSpinner';
import { RatingSelector } from '../../../../../components/RatingSelector';

interface FeedbackData {
  id: string;
  cycle_name: string;
  overall_rating: number;
  manager_feedback: {
    competencies: Array<{
      id: string;
      name: string;
      rating: number;
      comments: string;
      evidence: string[];
    }>;
    overall_comments: string;
    strengths: string[];
    development_areas: string[];
  };
  peer_feedback?: Array<{
    peer_name: string;
    comments: string;
    key_points: string[];
  }>;
  self_evaluation: {
    competencies: Array<{
      id: string;
      rating: number;
      comments: string;
    }>;
    overall_comments: string;
  };
  action_plan?: {
    goals: Array<{
      title: string;
      description: string;
      timeline: string;
    }>;
  };
}

export default function FeedbackPage() {
  const params = useParams();
  const router = useRouter();
  const [feedback, setFeedback] = useState<FeedbackData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchFeedback = async () => {
      try {
        const response = await fetch(`/api/employee/evaluations/${params.id}/feedback`);
        const data = await response.json();
        setFeedback(data);
      } catch (error) {
        console.error('Failed to fetch feedback:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFeedback();
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!feedback) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">Feedback not available</h2>
        <Button onClick={() => router.push('/employee')} className="mt-4">
          Back to Evaluations
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Performance Feedback"
        description={`Your evaluation results for ${feedback.cycle_name}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'My Evaluations', href: '/employee' },
          { label: 'Evaluation', href: `/employee/evaluations/${params.id}` },
          { label: 'Feedback', href: `/employee/evaluations/${params.id}/feedback` },
        ]}
      />

      {/* Overall Rating */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-4">Overall Performance Rating</h2>
          <div className="flex justify-center mb-4">
            <RatingSelector
              value={feedback.overall_rating}
              onChange={() => {}}
              disabled
              size="large"
            />
          </div>
          <Badge variant="info" className="text-lg px-4 py-2">
            {feedback.overall_rating.toFixed(1)} / 5.0
          </Badge>
        </div>
      </Card>

      {/* Manager Feedback */}
      <Card className="p-6">
        <h2 className="text-2xl font-semibold mb-6">Manager Evaluation</h2>

        {/* Competencies */}
        <div className="space-y-6">
          {feedback.manager_feedback.competencies.map((competency) => (
            <div key={competency.id} className="border-b border-gray-200 pb-6 last:border-0">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold">{competency.name}</h3>
                <div className="flex items-center gap-2">
                  <RatingSelector value={competency.rating} onChange={() => {}} disabled />
                  <span className="text-sm text-gray-600">{competency.rating}/5</span>
                </div>
              </div>
              <p className="text-gray-700 mb-3">{competency.comments}</p>
              {competency.evidence.length > 0 && (
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm font-medium text-gray-700 mb-2">Evidence:</div>
                  <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                    {competency.evidence.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Overall Comments */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-semibold mb-2">Manager's Overall Comments</h4>
          <p className="text-gray-700">{feedback.manager_feedback.overall_comments}</p>
        </div>

        {/* Strengths and Development Areas */}
        <div className="grid md:grid-cols-2 gap-6 mt-6">
          <div>
            <h4 className="font-semibold text-green-900 mb-3">Key Strengths</h4>
            <ul className="space-y-2">
              {feedback.manager_feedback.strengths.map((strength, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span className="text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-orange-900 mb-3">Development Areas</h4>
            <ul className="space-y-2">
              {feedback.manager_feedback.development_areas.map((area, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-orange-600 mt-1">→</span>
                  <span className="text-gray-700">{area}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {/* Peer Feedback Summary */}
      {feedback.peer_feedback && feedback.peer_feedback.length > 0 && (
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-4">Peer Feedback Summary</h2>
          <div className="space-y-4">
            {feedback.peer_feedback.map((peer, idx) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                <div className="font-medium text-gray-900 mb-2">From: {peer.peer_name}</div>
                <p className="text-gray-700 mb-3">{peer.comments}</p>
                {peer.key_points.length > 0 && (
                  <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                    {peer.key_points.map((point, pidx) => (
                      <li key={pidx}>{point}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Self-Evaluation Comparison */}
      <Card className="p-6">
        <h2 className="text-2xl font-semibold mb-4">Your Self-Evaluation</h2>
        <p className="text-gray-700 mb-4">{feedback.self_evaluation.overall_comments}</p>

        <div className="space-y-3">
          {feedback.self_evaluation.competencies.map((comp) => {
            const managerComp = feedback.manager_feedback.competencies.find(c => c.id === comp.id);
            return (
              <div key={comp.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm">{managerComp?.name}</span>
                <div className="flex gap-4">
                  <div className="text-sm">
                    <span className="text-gray-600">Self: </span>
                    <span className="font-medium">{comp.rating}/5</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-600">Manager: </span>
                    <span className="font-medium">{managerComp?.rating}/5</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Action Plan */}
      {feedback.action_plan && (
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-4">Development Action Plan</h2>
          <div className="space-y-4">
            {feedback.action_plan.goals.map((goal, idx) => (
              <div key={idx} className="p-4 border border-gray-200 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">{goal.title}</h4>
                <p className="text-gray-700 mb-2">{goal.description}</p>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Timeline:</span> {goal.timeline}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Actions */}
      <div className="flex gap-3 justify-between">
        <Button
          variant="outline"
          onClick={() => router.push('/employee')}
        >
          Back to Evaluations
        </Button>
        <div className="flex gap-3">
          <Button variant="secondary">
            Download PDF
          </Button>
          <Button variant="secondary">
            Schedule Follow-up
          </Button>
        </div>
      </div>
    </div>
  );
}
