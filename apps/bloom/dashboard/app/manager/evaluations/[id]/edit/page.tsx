'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { PageHeader } from '../../../../../components/PageHeader';
import { FeedbackForm } from '../../../../../components/FeedbackForm';
import { RatingSelector } from '../../../../../components/RatingSelector';
import { Card } from '../../../../../components/Card';
import { Button } from '../../../../../components/Button';
import { LoadingSpinner } from '../../../../../components/LoadingSpinner';
import { AlertBanner } from '../../../../../components/AlertBanner';
import { Badge } from '../../../../../components/Badge';

interface EvaluationData {
  id: string;
  employee_name: string;
  cycle_name: string;
  competencies: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  existing_draft?: {
    responses: Record<string, {
      rating: number;
      comments: string;
      evidence: string[];
    }>;
    overall_rating: number;
    overall_comments: string;
    strengths: string[];
    development_areas: string[];
  };
}

export default function EditEvaluationPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const fromAIDraft = searchParams.get('source') === 'ai-draft';

  const [evalData, setEvalData] = useState<EvaluationData | null>(null);
  const [responses, setResponses] = useState<Record<string, { rating: number; comments: string; evidence: string[] }>>({});
  const [overallRating, setOverallRating] = useState(0);
  const [overallComments, setOverallComments] = useState('');
  const [strengths, setStrengths] = useState<string[]>(['']);
  const [developmentAreas, setDevelopmentAreas] = useState<string[]>(['']);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvalData = async () => {
      try {
        const endpoint = fromAIDraft
          ? `/api/manager/evaluations/${params.id}/ai-draft`
          : `/api/manager/evaluations/${params.id}/draft`;

        const response = await fetch(endpoint);
        const data = await response.json();
        setEvalData(data);

        if (data.existing_draft || fromAIDraft) {
          const draft = data.existing_draft || data;
          setResponses(draft.responses || {});
          setOverallRating(draft.overall_rating || 0);
          setOverallComments(draft.overall_comments || draft.overall_summary || '');
          setStrengths(draft.strengths || ['']);
          setDevelopmentAreas(draft.development_areas || ['']);
        }
      } catch (error) {
        console.error('Failed to fetch evaluation data:', error);
        setError('Failed to load evaluation form');
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvalData();
  }, [params.id, fromAIDraft]);

  const handleSaveDraft = async () => {
    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch(`/api/manager/evaluations/${params.id}/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          responses,
          overall_rating: overallRating,
          overall_comments: overallComments,
          strengths: strengths.filter(s => s.trim()),
          development_areas: developmentAreas.filter(d => d.trim()),
        }),
      });

      if (!response.ok) throw new Error('Failed to save draft');

      alert('Draft saved successfully');
    } catch (error) {
      setError('Failed to save draft. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddStrength = () => {
    setStrengths([...strengths, '']);
  };

  const handleAddDevelopmentArea = () => {
    setDevelopmentAreas([...developmentAreas, '']);
  };

  const handleSubmit = () => {
    router.push(`/manager/evaluations/${params.id}/submit`);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!evalData) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">Evaluation not found</h2>
        <Button onClick={() => router.push('/manager')} className="mt-4">
          Back to Team Evaluations
        </Button>
      </div>
    );
  }

  const allRated = evalData.competencies.every(c => responses[c.id]?.rating > 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Edit Evaluation: ${evalData.employee_name}`}
        description={evalData.cycle_name}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Team Evaluations', href: '/manager' },
          { label: evalData.employee_name, href: `/manager/evaluations/${params.id}` },
          { label: 'Edit', href: `/manager/evaluations/${params.id}/edit` },
        ]}
      />

      {fromAIDraft && (
        <AlertBanner
          type="info"
          message="You're editing from the AI draft. Feel free to modify any section to match your assessment."
        />
      )}

      {error && (
        <AlertBanner type="error" message={error} />
      )}

      {/* Overall Rating */}
      <Card className="p-6 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
        <h2 className="text-xl font-semibold mb-4">Overall Performance Rating</h2>
        <div className="flex items-center gap-4">
          <RatingSelector
            value={overallRating}
            onChange={setOverallRating}
            size="large"
          />
          <div className="text-2xl font-bold text-purple-600">
            {overallRating > 0 ? `${overallRating}/5` : 'Not rated'}
          </div>
        </div>
      </Card>

      {/* Competency Evaluations */}
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Competency Ratings</h2>

        {evalData.competencies.map((competency, index) => (
          <Card key={competency.id} className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold">{competency.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{competency.description}</p>
              </div>
              <Badge variant="default">{index + 1} of {evalData.competencies.length}</Badge>
            </div>

            <FeedbackForm
              competencyId={competency.id}
              value={responses[competency.id] || { rating: 0, comments: '', evidence: [] }}
              onChange={(value) => setResponses({ ...responses, [competency.id]: value })}
              showRating
              showEvidence
            />
          </Card>
        ))}
      </div>

      {/* Strengths */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Key Strengths</h2>
        <div className="space-y-3">
          {strengths.map((strength, index) => (
            <div key={index} className="flex gap-3">
              <input
                type="text"
                value={strength}
                onChange={(e) => {
                  const newStrengths = [...strengths];
                  newStrengths[index] = e.target.value;
                  setStrengths(newStrengths);
                }}
                placeholder="Describe a key strength..."
                className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {strengths.length > 1 && (
                <Button
                  variant="outline"
                  onClick={() => setStrengths(strengths.filter((_, i) => i !== index))}
                >
                  Remove
                </Button>
              )}
            </div>
          ))}
          <Button variant="outline" onClick={handleAddStrength}>
            + Add Strength
          </Button>
        </div>
      </Card>

      {/* Development Areas */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Development Areas</h2>
        <div className="space-y-3">
          {developmentAreas.map((area, index) => (
            <div key={index} className="flex gap-3">
              <input
                type="text"
                value={area}
                onChange={(e) => {
                  const newAreas = [...developmentAreas];
                  newAreas[index] = e.target.value;
                  setDevelopmentAreas(newAreas);
                }}
                placeholder="Describe an area for development..."
                className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {developmentAreas.length > 1 && (
                <Button
                  variant="outline"
                  onClick={() => setDevelopmentAreas(developmentAreas.filter((_, i) => i !== index))}
                >
                  Remove
                </Button>
              )}
            </div>
          ))}
          <Button variant="outline" onClick={handleAddDevelopmentArea}>
            + Add Development Area
          </Button>
        </div>
      </Card>

      {/* Overall Comments */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Overall Comments</h2>
        <textarea
          value={overallComments}
          onChange={(e) => setOverallComments(e.target.value)}
          placeholder="Provide an overall summary of the employee's performance, achievements, and recommendations..."
          className="w-full min-h-[200px] p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </Card>

      {/* Actions */}
      <div className="flex gap-3 justify-end sticky bottom-0 bg-white p-4 border-t border-gray-200 shadow-lg">
        <Button
          variant="outline"
          onClick={() => router.push(`/manager/evaluations/${params.id}`)}
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
          disabled={!allRated || overallRating === 0}
        >
          Continue to Submit
        </Button>
      </div>
    </div>
  );
}
