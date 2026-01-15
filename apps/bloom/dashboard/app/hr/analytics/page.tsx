'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '../../../components/PageHeader';
import { Card } from '../../../components/Card';
import { Select } from '../../../components/Select';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { EvaluationChart } from '../../../components/EvaluationChart';

interface AnalyticsData {
  overview: {
    total_evaluations: number;
    avg_rating: number;
    completion_rate: number;
    on_time_completion: number;
  };
  rating_distribution: number[];
  department_performance: Array<{
    department: string;
    avg_rating: number;
    count: number;
  }>;
  trends: {
    labels: string[];
    ratings: number[];
  };
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [cycleFilter, setCycleFilter] = useState('current');

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch(`/api/hr/analytics?cycle=${cycleFilter}`);
        const data = await response.json();
        setAnalytics(data);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, [cycleFilter]);

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
        title="Analytics & Reports"
        description="Comprehensive performance evaluation insights"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'HR Dashboard', href: '/hr' },
          { label: 'Analytics', href: '/hr/analytics' },
        ]}
      />

      {/* Filters */}
      <Card className="p-4">
        <Select
          label="Cycle"
          value={cycleFilter}
          onChange={(e) => setCycleFilter(e.target.value)}
          options={[
            { value: 'current', label: 'Current Cycle' },
            { value: 'q4_2024', label: 'Q4 2024' },
            { value: 'q3_2024', label: 'Q3 2024' },
            { value: 'all_time', label: 'All Time' },
          ]}
        />
      </Card>

      {/* Overview Metrics */}
      <div className="grid md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Total Evaluations</div>
          <div className="text-3xl font-bold text-blue-600">
            {analytics?.overview.total_evaluations || 0}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Average Rating</div>
          <div className="text-3xl font-bold text-green-600">
            {analytics?.overview.avg_rating?.toFixed(1) || '—'}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">Completion Rate</div>
          <div className="text-3xl font-bold text-purple-600">
            {analytics?.overview.completion_rate || 0}%
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-gray-600 mb-2">On-Time Completion</div>
          <div className="text-3xl font-bold text-orange-600">
            {analytics?.overview.on_time_completion || 0}%
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Rating Distribution */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Rating Distribution</h2>
          <EvaluationChart data={analytics?.rating_distribution || []} />
        </Card>

        {/* Performance Trends */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Performance Trends</h2>
          <EvaluationChart data={analytics?.trends.ratings || []} />
        </Card>
      </div>

      {/* Department Performance */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Department Performance</h2>
        <div className="space-y-4">
          {analytics?.department_performance.map((dept) => (
            <div key={dept.department} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium">{dept.department}</div>
                <div className="text-sm text-gray-600">{dept.count} evaluations</div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {dept.avg_rating.toFixed(1)}
                </div>
                <div className="text-sm text-gray-600">avg rating</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Export Options */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Export Reports</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all">
            <div className="font-medium">📊 Excel Report</div>
            <div className="text-sm text-gray-600 mt-1">Detailed evaluation data</div>
          </button>

          <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all">
            <div className="font-medium">📄 PDF Summary</div>
            <div className="text-sm text-gray-600 mt-1">Executive summary</div>
          </button>

          <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all">
            <div className="font-medium">📈 Charts & Graphs</div>
            <div className="text-sm text-gray-600 mt-1">Visual analytics</div>
          </button>
        </div>
      </Card>
    </div>
  );
}
