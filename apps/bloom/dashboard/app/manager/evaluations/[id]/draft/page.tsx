'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PageHeader } from '../../../../../components/PageHeader';
import { ManagerDraftView } from '../../../../../components/ManagerDraftView';
import { ClarifyingQuestions } from '../../../../../components/ClarifyingQuestions';
import { EvidenceMap } from '../../../../../components/EvidenceMap';
import { Card } from '../../../../../components/Card';
import { Button } from '../../../../../components/Button';
import { Badge } from '../../../../../components/Badge';
import { LoadingSpinner } from '../../../../../components/LoadingSpinner';
import { AlertBanner } from '../../../../../components/AlertBanner';

interface AIDraft {
  id: string;
  employee_name: string;
  overall_rating: number;
  competencies: Array<{
    id: string;
    name: string;
    rating: number;
    rationale: string;
    evidence: string[];
    confidence: number;
  }>;
  overall_summary: string;
  strengths: string[];
  development_areas: string[];
  clarifying_questions: Array<{
    question: string;
    context: string;
    importance: 'high' | 'medium' | 'low';
  }>;
  evidence_map: {
    self_eval: any;
    peer_feedback: any[];
    manager_notes: any[];
  };
}

export default function AIDraftPage() {
  const params = useParams();
  const router = useRouter();
  const [draft, setDraft] = useState<AIDraft | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showQuestions, setShowQuestions] = useState(true);

  useEffect(() => {
    const fetchDraft = async () => {
      try {
        const response = await fetch(`/api/manager/evaluations/${params.id}/ai-draft`);
        const data = await response.json();
        setDraft(data);
      } catch (error) {
        console.error('Failed to fetch AI draft:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDraft();
  }, [params.id]);

  const handleAcceptDraft = () => {
    // Navigate to edit page with draft pre-filled
    router.push(`/manager/evaluations/${params.id}/edit?source=ai-draft`);
  };

  const handleStartFromScratch = () => {
    router.push(`/manager/evaluations/${params.id}/edit`);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">AI Draft not available</h2>
        <Button onClick={() => router.push(`/manager/evaluations/${params.id}`)} className="mt-4">
          Back to Evaluation
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`AI Draft: ${draft.employee_name}`}
        description="Review AI-generated evaluation and supporting evidence"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Team Evaluations', href: '/manager' },
          { label: draft.employee_name, href: `/manager/evaluations/${params.id}` },
          { label: 'AI Draft', href: `/manager/evaluations/${params.id}/draft` },
        ]}
      />

      <AlertBanner
        type="info"
        message="This AI-generated draft is based on self-evaluation, peer feedback, and available performance data. Review carefully and adjust as needed."
      />

      {/* Draft Overview */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">AI-Generated Evaluation</h2>
          <Badge variant="info">AI Draft</Badge>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <div className="text-sm text-gray-600 mb-2">Overall Rating</div>
            <div className="text-3xl font-bold text-blue-600">
              {draft.overall_rating.toFixed(1)} / 5.0
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-2">Average Confidence</div>
            <div className="text-3xl font-bold text-blue-600">
              {(draft.competencies.reduce((acc, c) => acc + c.confidence, 0) / draft.competencies.length * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </Card>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Clarifying Questions */}
          {showQuestions && draft.clarifying_questions.length > 0 && (
            <Card className="p-6 border-orange-200 bg-orange-50">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-semibold text-orange-900">
                  Questions to Consider
                </h2>
                <button
                  onClick={() => setShowQuestions(false)}
                  className="text-sm text-orange-700 hover:text-orange-900"
                >
                  Dismiss
                </button>
              </div>
              <ClarifyingQuestions questions={draft.clarifying_questions} />
            </Card>
          )}

          {/* Draft Content */}
          <ManagerDraftView draft={draft} />

          {/* Actions */}
          <div className="flex gap-3 justify-end sticky bottom-0 bg-white p-4 border-t border-gray-200 shadow-lg">
            <Button
              variant="outline"
              onClick={handleStartFromScratch}
            >
              Start from Scratch
            </Button>
            <Button
              variant="secondary"
              onClick={() => router.push(`/manager/evaluations/${params.id}`)}
            >
              Save for Later
            </Button>
            <Button
              variant="primary"
              onClick={handleAcceptDraft}
            >
              Use This Draft
            </Button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Evidence Map */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Evidence Sources</h2>
            <EvidenceMap evidenceMap={draft.evidence_map} />
          </Card>

          {/* AI Insights */}
          <Card className="p-6 bg-purple-50 border-purple-200">
            <h3 className="font-semibold text-purple-900 mb-3">AI Analysis Notes</h3>
            <div className="text-sm text-purple-800 space-y-2">
              <p>
                • Analyzed {draft.evidence_map.peer_feedback.length} peer reviews
              </p>
              <p>
                • Cross-referenced with self-evaluation
              </p>
              <p>
                • Identified {draft.strengths.length} key strengths
              </p>
              <p>
                • Highlighted {draft.development_areas.length} growth areas
              </p>
            </div>
          </Card>

          {/* Tips */}
          <Card className="p-6 bg-blue-50 border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-3">Review Tips</h3>
            <ul className="text-sm text-blue-800 space-y-2 list-disc list-inside">
              <li>Verify ratings align with your observations</li>
              <li>Add specific examples from your experience</li>
              <li>Address any clarifying questions raised</li>
              <li>Adjust language to match your style</li>
              <li>Ensure feedback is actionable</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
