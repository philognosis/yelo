'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '../../../components/PageHeader';
import { Card } from '../../../components/Card';
import { Badge } from '../../../components/Badge';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { EvaluationChart } from '../../../components/EvaluationChart';
import Link from 'next/link';

interface TeamMember {
  id: string;
  name: string;
  role: string;
  department: string;
  current_evaluation: {
    id: string;
    status: string;
    overall_rating?: number;
  };
  performance_trend: number[];
}

export default function TeamOverviewPage() {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchTeamData = async () => {
      try {
        const response = await fetch('/api/manager/team');
        const data = await response.json();
        setTeamMembers(data);
      } catch (error) {
        console.error('Failed to fetch team data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTeamData();
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  const avgRating = teamMembers.reduce((acc, m) =>
    acc + (m.current_evaluation.overall_rating || 0), 0
  ) / teamMembers.filter(m => m.current_evaluation.overall_rating).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team Overview"
        description="Monitor your team's performance and evaluation progress"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Team Evaluations', href: '/manager' },
          { label: 'Team Overview', href: '/manager/team' },
        ]}
      />

      {/* Team Metrics */}
      <div className="grid md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Team Size</div>
          <div className="text-3xl font-bold text-blue-600">{teamMembers.length}</div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Average Rating</div>
          <div className="text-3xl font-bold text-green-600">
            {avgRating ? avgRating.toFixed(1) : '—'}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Completed</div>
          <div className="text-3xl font-bold text-purple-600">
            {teamMembers.filter(m => m.current_evaluation.status === 'completed').length}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">In Progress</div>
          <div className="text-3xl font-bold text-orange-600">
            {teamMembers.filter(m => m.current_evaluation.status !== 'completed').length}
          </div>
        </Card>
      </div>

      {/* Team Members */}
      <Card className="p-6">
        <h2 className="text-2xl font-semibold mb-6">Team Members</h2>
        <div className="space-y-4">
          {teamMembers.map((member) => (
            <Link
              key={member.id}
              href={`/manager/evaluations/${member.current_evaluation.id}`}
              className="block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold">{member.name}</h3>
                    <Badge variant="default">{member.role}</Badge>
                    <Badge
                      variant={
                        member.current_evaluation.status === 'completed' ? 'success' :
                        member.current_evaluation.status === 'manager_review' ? 'warning' :
                        'default'
                      }
                    >
                      {member.current_evaluation.status.replace('_', ' ')}
                    </Badge>
                  </div>
                  <div className="text-sm text-gray-600 mt-1">{member.department}</div>
                </div>

                {member.current_evaluation.overall_rating && (
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Rating</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {member.current_evaluation.overall_rating.toFixed(1)}
                    </div>
                  </div>
                )}
              </div>

              {/* Performance Trend */}
              {member.performance_trend.length > 0 && (
                <div className="mt-4">
                  <div className="text-sm text-gray-600 mb-2">Performance Trend</div>
                  <EvaluationChart data={member.performance_trend} compact />
                </div>
              )}
            </Link>
          ))}
        </div>
      </Card>

      {/* Team Performance Chart */}
      <Card className="p-6">
        <h2 className="text-2xl font-semibold mb-6">Team Performance Distribution</h2>
        <EvaluationChart
          data={teamMembers
            .filter(m => m.current_evaluation.overall_rating)
            .map(m => m.current_evaluation.overall_rating!)}
        />
      </Card>
    </div>
  );
}
