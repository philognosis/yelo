'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PageHeader } from '../../../../components/PageHeader';
import { Card } from '../../../../components/Card';
import { Badge } from '../../../../components/Badge';
import { Button } from '../../../../components/Button';
import { RatingSelector } from '../../../../components/RatingSelector';
import { LoadingSpinner } from '../../../../components/LoadingSpinner';
import { AlertBanner } from '../../../../components/AlertBanner';

interface CalibrationReview {
  id: string;
  employee_name: string;
  employee_role: string;
  manager_name: string;
  cycle_name: string;
  manager_rating: number;
  manager_evaluation: {
    competencies: Array<{
      name: string;
      rating: number;
      comments: string;
    }>;
    overall_comments: string;
    strengths: string[];
    development_areas: string[];
  };
  peer_ratings_avg?: number;
  self_rating?: number;
  peer_group_avg?: number;
  department_avg?: number;
  suggested_adjustment?: {
    rating: number;
    rationale: string;
  };
}

export default function CalibrationReviewPage() {
  const params = useParams();
  const router = useRouter();
  const [review, setReview] = useState<CalibrationReview | null>(null);
  const [calibratedRating, setCalibratedRating] = useState(0);
  const [adjustmentNotes, setAdjustmentNotes] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const fetchReview = async () => {
      try {
        const response = await fetch(`/api/committee/calibration/${params.id}`);
        const data = await response.json();
        setReview(data);
        setCalibratedRating(data.manager_rating);
      } catch (error) {
        console.error('Failed to fetch review:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReview();
  }, [params.id]);

  const handleApprove = async () => {
    setIsSubmitting(true);

    try {
      const response = await fetch(`/api/committee/calibration/${params.id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          calibrated_rating: calibratedRating,
          adjustment_notes: adjustmentNotes,
        }),
      });

      if (!response.ok) throw new Error('Failed to approve');

      router.push('/committee');
    } catch (error) {
      console.error('Failed to approve:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestChange = async () => {
    setIsSubmitting(true);

    try {
      const response = await fetch(`/api/committee/calibration/${params.id}/request-change`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          suggested_rating: calibratedRating,
          feedback: adjustmentNotes,
        }),
      });

      if (!response.ok) throw new Error('Failed to request change');

      router.push('/committee');
    } catch (error) {
      console.error('Failed to request change:', error);
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

  if (!review) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900">Review not found</h2>
        <Button onClick={() => router.push('/committee')} className="mt-4">
          Back to Committee Dashboard
        </Button>
      </div>
    );
  }

  const ratingDifference = Math.abs(calibratedRating - review.manager_rating);
  const significantChange = ratingDifference >= 0.5;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Calibration Review: ${review.employee_name}`}
        description={`${review.employee_role} • ${review.cycle_name}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Committee', href: '/committee' },
          { label: 'Calibration', href: '/committee/calibration' },
          { label: review.employee_name, href: `/committee/calibration/${params.id}` },
        ]}
      />

      {/* Suggested Adjustment */}
      {review.suggested_adjustment && (
        <AlertBanner
          type="warning"
          message={`AI suggests adjusting rating to ${review.suggested_adjustment.rating.toFixed(1)}: ${review.suggested_adjustment.rationale}`}
        />
      )}

      {/* Comparison Overview */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Rating Comparison</h2>
        <div className="grid md:grid-cols-5 gap-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-2">Manager Rating</div>
            <div className="text-3xl font-bold text-blue-600">
              {review.manager_rating.toFixed(1)}
            </div>
          </div>

          {review.self_rating && (
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-2">Self Rating</div>
              <div className="text-2xl font-bold text-gray-700">
                {review.self_rating.toFixed(1)}
              </div>
            </div>
          )}

          {review.peer_ratings_avg && (
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-2">Peer Avg</div>
              <div className="text-2xl font-bold text-gray-700">
                {review.peer_ratings_avg.toFixed(1)}
              </div>
            </div>
          )}

          {review.peer_group_avg && (
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-2">Peer Group Avg</div>
              <div className="text-2xl font-bold text-gray-700">
                {review.peer_group_avg.toFixed(1)}
              </div>
            </div>
          )}

          {review.department_avg && (
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-2">Dept Avg</div>
              <div className="text-2xl font-bold text-gray-700">
                {review.department_avg.toFixed(1)}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Calibrated Rating */}
      <Card className="p-6 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
        <h2 className="text-xl font-semibold mb-4">Committee Calibrated Rating</h2>
        <div className="flex items-center gap-6">
          <RatingSelector
            value={calibratedRating}
            onChange={setCalibratedRating}
            size="large"
          />
          <div>
            <div className="text-3xl font-bold text-purple-600">
              {calibratedRating}/5
            </div>
            {significantChange && (
              <Badge variant="warning" className="mt-2">
                Significant change from manager rating
              </Badge>
            )}
          </div>
        </div>
      </Card>

      {/* Manager Evaluation */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Manager Evaluation</h2>

        <div className="space-y-4">
          {review.manager_evaluation.competencies.map((comp, idx) => (
            <div key={idx} className="border-b border-gray-200 pb-4 last:border-0">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold">{comp.name}</h3>
                <div className="flex items-center gap-2">
                  <RatingSelector value={comp.rating} onChange={() => {}} disabled size="small" />
                  <span className="text-sm text-gray-600">{comp.rating}/5</span>
                </div>
              </div>
              <p className="text-gray-700">{comp.comments}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Overall Comments</h4>
          <p className="text-gray-700">{review.manager_evaluation.overall_comments}</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mt-6">
          <div>
            <h4 className="font-semibold text-green-900 mb-3">Strengths</h4>
            <ul className="space-y-2">
              {review.manager_evaluation.strengths.map((strength, idx) => (
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
              {review.manager_evaluation.development_areas.map((area, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-orange-600 mt-1">→</span>
                  <span className="text-gray-700">{area}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {/* Adjustment Notes */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Calibration Notes</h2>
        <textarea
          value={adjustmentNotes}
          onChange={(e) => setAdjustmentNotes(e.target.value)}
          placeholder="Provide rationale for the calibrated rating, especially if it differs from the manager's rating..."
          className="w-full min-h-[150px] p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </Card>

      {/* Actions */}
      <div className="flex gap-3 justify-between sticky bottom-0 bg-white p-4 border-t border-gray-200 shadow-lg">
        <Button
          variant="outline"
          onClick={() => router.push('/committee/calibration')}
          disabled={isSubmitting}
        >
          Back to List
        </Button>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={handleRequestChange}
            isLoading={isSubmitting}
            disabled={!significantChange}
          >
            Request Manager Review
          </Button>
          <Button
            variant="success"
            onClick={handleApprove}
            isLoading={isSubmitting}
          >
            Approve & Finalize
          </Button>
        </div>
      </div>
    </div>
  );
}
