'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PageHeader } from '../../../../../components/PageHeader';
import { Card } from '../../../../../components/Card';
import { Button } from '../../../../../components/Button';
import { Badge } from '../../../../../components/Badge';
import { LoadingSpinner } from '../../../../../components/LoadingSpinner';
import { AlertBanner } from '../../../../../components/AlertBanner';
import { RatingSelector } from '../../../../../components/RatingSelector';

interface SubmissionPreview {
  id: string;
  employee_name: string;
  cycle_name: string;
  overall_rating: number;
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
}

export default function SubmitEvaluationPage() {
  const params = useParams();
  const router = useRouter();
  const [preview, setPreview] = useState<SubmissionPreview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmChecks, setConfirmChecks] = useState({
    reviewed: false,
    accurate: false,
    actionable: false,
  });

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const response = await fetch(`/api/manager/evaluations/${params.id}/preview`);
        const data = await response.json();
        setPreview(data);
      } catch (error) {
        console.error('Failed to fetch preview:', error);
        setError('Failed to load evaluation preview');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPreview();
  }, [params.id]);

  const handleSubmit = async () => {
    if (!Object.values(confirmChecks).every(Boolean)) {
      setError('Please confirm all checkboxes before submitting');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`/api/manager/evaluations/${params.id}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) throw new Error('Failed to submit evaluation');

      router.push(`/manager/evaluations/${params.id}?submitted=true`);
    } catch (error) {
      setError('Failed to submit evaluation. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">Preview not available</h2>
        <Button onClick={() => router.push(`/manager/evaluations/${params.id}/edit`)} className="mt-4">
          Back to Edit
        </Button>
      </div>
    );
  }

  const allConfirmed = Object.values(confirmChecks).every(Boolean);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Submit Evaluation: ${preview.employee_name}`}
        description="Review and submit your final evaluation"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Team Evaluations', href: '/manager' },
          { label: preview.employee_name, href: `/manager/evaluations/${params.id}` },
          { label: 'Submit', href: `/manager/evaluations/${params.id}/submit` },
        ]}
      />

      <AlertBanner
        type="warning"
        message="Please review carefully. Once submitted, this evaluation will be sent to HR and the committee for review."
      />

      {error && (
        <AlertBanner type="error" message={error} />
      )}

      {/* Overall Rating Preview */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-4">Overall Performance Rating</h2>
          <div className="flex justify-center mb-4">
            <RatingSelector
              value={preview.overall_rating}
              onChange={() => {}}
              disabled
              size="large"
            />
          </div>
          <Badge variant="info" className="text-lg px-4 py-2">
            {preview.overall_rating}/5
          </Badge>
        </div>
      </Card>

      {/* Competencies Summary */}
      <Card className="p-6">
        <h2 className="text-2xl font-semibold mb-6">Competency Ratings</h2>
        <div className="space-y-6">
          {preview.competencies.map((comp) => (
            <div key={comp.id} className="border-b border-gray-200 pb-6 last:border-0">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold">{comp.name}</h3>
                <div className="flex items-center gap-2">
                  <RatingSelector value={comp.rating} onChange={() => {}} disabled />
                  <span className="text-sm text-gray-600">{comp.rating}/5</span>
                </div>
              </div>
              <p className="text-gray-700 mb-3">{comp.comments}</p>
              {comp.evidence.length > 0 && (
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm font-medium text-gray-700 mb-2">Evidence:</div>
                  <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                    {comp.evidence.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Strengths and Development Areas */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-green-900 mb-4">Key Strengths</h2>
          <ul className="space-y-2">
            {preview.strengths.map((strength, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-green-600 mt-1">✓</span>
                <span className="text-gray-700">{strength}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold text-orange-900 mb-4">Development Areas</h2>
          <ul className="space-y-2">
            {preview.development_areas.map((area, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-orange-600 mt-1">→</span>
                <span className="text-gray-700">{area}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {/* Overall Comments */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Overall Comments</h2>
        <p className="text-gray-700 whitespace-pre-wrap">{preview.overall_comments}</p>
      </Card>

      {/* Confirmation Checklist */}
      <Card className="p-6 bg-yellow-50 border-yellow-200">
        <h2 className="text-xl font-semibold mb-4">Pre-Submission Checklist</h2>
        <div className="space-y-3">
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              checked={confirmChecks.reviewed}
              onChange={(e) => setConfirmChecks({ ...confirmChecks, reviewed: e.target.checked })}
              className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">I have thoroughly reviewed all ratings and comments</div>
              <div className="text-sm text-gray-600">All sections are complete and accurate</div>
            </div>
          </label>

          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              checked={confirmChecks.accurate}
              onChange={(e) => setConfirmChecks({ ...confirmChecks, accurate: e.target.checked })}
              className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">The evaluation accurately reflects the employee's performance</div>
              <div className="text-sm text-gray-600">Based on observations and available feedback</div>
            </div>
          </label>

          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              checked={confirmChecks.actionable}
              onChange={(e) => setConfirmChecks({ ...confirmChecks, actionable: e.target.checked })}
              className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <div className="font-medium">Feedback is constructive and actionable</div>
              <div className="text-sm text-gray-600">Provides clear guidance for growth and development</div>
            </div>
          </label>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex gap-3 justify-between sticky bottom-0 bg-white p-4 border-t border-gray-200 shadow-lg">
        <Button
          variant="outline"
          onClick={() => router.push(`/manager/evaluations/${params.id}/edit`)}
          disabled={isSubmitting}
        >
          ← Back to Edit
        </Button>
        <Button
          variant="success"
          onClick={handleSubmit}
          isLoading={isSubmitting}
          disabled={!allConfirmed}
        >
          Submit Evaluation
        </Button>
      </div>
    </div>
  );
}
