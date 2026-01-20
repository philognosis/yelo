'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import PageHeader from '@/components/PageHeader';
import Card from '@/components/Card';
import Button from '@/components/Button';
import LoadingSpinner from '@/components/LoadingSpinner';
import AlertBanner from '@/components/AlertBanner';

interface SelfEvalData {
  id: string;
  cycle_name: string;
  competencies: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  existing_eval?: {
    responses: Record<string, {
      rating: number;
      comments: string;
    }>;
    overall_comments: string;
  };
}

export default function SelfEvaluationPage() {
  const params = useParams();
  const router = useRouter();
  const [evalData, setEvalData] = useState<SelfEvalData | null>(null);
  const [responses, setResponses] = useState<Record<string, { rating: number; comments: string }>>({});
  const [overallComments, setOverallComments] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvalData = async () => {
      try {
        const response = await fetch(`/api/employee/evaluations/${params?.id || ""}/self-eval`);
        const data = await response.json();
        setEvalData(data);

        if (data.existing_eval) {
          setResponses(data.existing_eval.responses);
          setOverallComments(data.existing_eval.overall_comments);
        }
      } catch (error) {
        console.error('Failed to fetch evaluation data:', error);
        setError('Failed to load evaluation form');
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvalData();
  }, [params?.id]);

  const handleSaveDraft = async () => {
    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch(`/api/employee/evaluations/${params?.id || ""}/self-eval/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses, overall_comments: overallComments }),
      });

      if (!response.ok) throw new Error('Failed to save draft');

      // Show success message
      alert('Draft saved successfully');
    } catch (error) {
      setError('Failed to save draft. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSubmit = async () => {
    // Validate all competencies are rated
    const allRated = evalData?.competencies.every(c => (responses[c.id]?.rating ?? 0) > 0);

    if (!allRated) {
      setError('Please rate all competencies before submitting');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch(`/api/employee/evaluations/${params?.id || ""}/self-eval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses, overall_comments: overallComments }),
      });

      if (!response.ok) throw new Error('Failed to submit evaluation');

      router.push(`/employee/evaluations/${params?.id || ""}`);
    } catch (error) {
      setError('Failed to submit evaluation. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  if (!evalData) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">Evaluation not found</h2>
        <Button onClick={() => router.push('/employee')} className="mt-4">
          Back to Evaluations
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Self-Evaluation"
        description={`Complete your self-evaluation for ${evalData.cycle_name}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'My Evaluations', href: '/employee' },
          { label: 'Evaluation', href: `/employee/evaluations/${params?.id || ""}` },
          { label: 'Self-Evaluation', href: `/employee/evaluations/${params?.id || ""}/self-eval` },
        ]}
      />

      <AlertBanner
        alerts={[{
          id: 'self-eval-info',
          type: 'info',
          title: 'Self-Evaluation',
          message: 'Take your time to thoughtfully evaluate your performance. Your responses will be reviewed by your manager and used in your final evaluation.'
        }]}
      />

      {error && (
        <AlertBanner alerts={[{
          id: 'self-eval-error',
          type: 'error',
          title: 'Error',
          message: error
        }]} />
      )}

      {/* Evaluation Form */}
      <div className="space-y-6">
        {evalData.competencies.map((competency) => (
          <Card key={competency.id} className="p-6">
            <h3 className="text-lg font-semibold mb-2">{competency.name}</h3>
            <p className="text-sm text-gray-600 mb-4">{competency.description}</p>

            <div className="space-y-4">
              {/* Rating */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rating (1-5)
                </label>
                <select
                  value={responses[competency.id]?.rating || 0}
                  onChange={(e) => setResponses({
                    ...responses,
                    [competency.id]: {
                      ...responses[competency.id],
                      rating: parseInt(e.target.value),
                      comments: responses[competency.id]?.comments || ''
                    }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={0}>Select a rating</option>
                  <option value={1}>1 - Needs Improvement</option>
                  <option value={2}>2 - Below Expectations</option>
                  <option value={3}>3 - Meets Expectations</option>
                  <option value={4}>4 - Exceeds Expectations</option>
                  <option value={5}>5 - Outstanding</option>
                </select>
              </div>

              {/* Comments */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Comments
                </label>
                <textarea
                  value={responses[competency.id]?.comments || ''}
                  onChange={(e) => setResponses({
                    ...responses,
                    [competency.id]: {
                      rating: responses[competency.id]?.rating || 0,
                      comments: e.target.value
                    }
                  })}
                  placeholder="Provide details about your self-assessment..."
                  className="w-full min-h-[100px] p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </Card>
        ))}

        {/* Overall Comments */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Overall Comments</h3>
          <textarea
            value={overallComments}
            onChange={(e) => setOverallComments(e.target.value)}
            placeholder="Share any additional thoughts about your performance, achievements, challenges, or goals..."
            className="w-full min-h-[150px] p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </Card>

        {/* Actions */}
        <div className="flex gap-3 justify-end sticky bottom-0 bg-white p-4 border-t border-gray-200 shadow-lg">
          <Button
            variant="ghost"
            onClick={() => router.push(`/employee/evaluations/${params?.id || ""}`)}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button
            variant="secondary"
            onClick={handleSaveDraft}
            isLoading={isSaving}
          >
            Save Draft
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            isLoading={isSaving}
          >
            Submit Evaluation
          </Button>
        </div>
      </div>

      {/* Guidelines */}
      <Card className="p-6 bg-green-50 border-green-200">
        <h3 className="font-semibold text-green-900 mb-2">Self-Evaluation Tips</h3>
        <ul className="text-sm text-green-800 space-y-1 list-disc list-inside">
          <li>Be honest and specific about your accomplishments and areas for growth</li>
          <li>Provide concrete examples to support your ratings</li>
          <li>Consider feedback you've received throughout the review period</li>
          <li>Focus on both technical skills and soft skills</li>
          <li>Save your draft frequently to avoid losing your work</li>
        </ul>
      </Card>
    </div>
  );
}
