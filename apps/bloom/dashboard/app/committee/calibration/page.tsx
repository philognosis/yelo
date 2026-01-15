'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '../../../components/PageHeader';
import { Card } from '../../../components/Card';
import { Badge } from '../../../components/Badge';
import { Button } from '../../../components/Button';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import Link from 'next/link';

interface CalibrationSession {
  evaluations: Array<{
    id: string;
    employee_name: string;
    manager_name: string;
    manager_rating: number;
    suggested_rating?: number;
    department: string;
    status: string;
  }>;
}

export default function CalibrationSessionPage() {
  const [session, setSession] = useState<CalibrationSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEvaluations, setSelectedEvaluations] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const response = await fetch('/api/committee/calibration/session');
        const data = await response.json();
        setSession(data);
      } catch (error) {
        console.error('Failed to fetch calibration session:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSession();
  }, []);

  const toggleSelection = (id: string) => {
    const newSelection = new Set(selectedEvaluations);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedEvaluations(newSelection);
  };

  const handleStartSession = () => {
    // Start calibration session with selected evaluations
    console.log('Starting session with:', Array.from(selectedEvaluations));
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Calibration Session"
        description="Review and calibrate performance ratings across teams"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Committee', href: '/committee' },
          { label: 'Calibration', href: '/committee/calibration' },
        ]}
        action={
          <Button
            variant="primary"
            onClick={handleStartSession}
            disabled={selectedEvaluations.size === 0}
          >
            Start Calibration ({selectedEvaluations.size})
          </Button>
        }
      />

      {/* Session Info */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h2 className="text-xl font-semibold mb-4">Session Guidelines</h2>
        <ul className="text-sm text-blue-800 space-y-2 list-disc list-inside">
          <li>Review ratings for consistency across teams and departments</li>
          <li>Consider relative performance within peer groups</li>
          <li>Ensure rating distribution follows organizational guidelines</li>
          <li>Flag evaluations that require discussion or adjustment</li>
          <li>Document rationale for any rating changes</li>
        </ul>
      </Card>

      {/* Rating Distribution */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Rating Distribution</h2>
        <div className="grid grid-cols-5 gap-4">
          {[5, 4, 3, 2, 1].map((rating) => {
            const count = session?.evaluations.filter(e => Math.round(e.manager_rating) === rating).length || 0;
            const percentage = session ? (count / session.evaluations.length * 100).toFixed(0) : 0;

            return (
              <div key={rating} className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">{count}</div>
                <div className="text-sm text-gray-600 mb-2">{rating} Stars</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">{percentage}%</div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Evaluations List */}
      <Card className="overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Evaluations for Calibration</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvaluations(new Set(session?.evaluations.map(ev => ev.id)));
                      } else {
                        setSelectedEvaluations(new Set());
                      }
                    }}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Manager
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Manager Rating
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Suggested
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {session?.evaluations.map((evaluation) => (
                <tr key={evaluation.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedEvaluations.has(evaluation.id)}
                      onChange={() => toggleSelection(evaluation.id)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{evaluation.employee_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-gray-700">{evaluation.manager_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-gray-700">{evaluation.department}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-lg font-bold text-blue-600">
                      {evaluation.manager_rating.toFixed(1)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {evaluation.suggested_rating ? (
                      <div className="text-lg font-bold text-green-600">
                        {evaluation.suggested_rating.toFixed(1)}
                      </div>
                    ) : (
                      <div className="text-gray-400">—</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant="default">{evaluation.status}</Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/committee/calibration/${evaluation.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      Review →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
