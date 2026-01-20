'use client';

import { useEffect, useState } from 'react';
import PageHeader from '@/components/PageHeader';
import Card from '@/components/Card';
import Badge from '@/components/Badge';
import Input from '@/components/Input';
import Select from '@/components/Select';
import LoadingSpinner from '@/components/LoadingSpinner';
import Link from 'next/link';

interface Evaluation {
  id: string;
  employee_name: string;
  manager_name: string;
  cycle_name: string;
  status: string;
  overall_rating?: number;
  last_updated: string;
}

export default function AllEvaluationsPage() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [cycleFilter, setCycleFilter] = useState('all');

  useEffect(() => {
    const fetchEvaluations = async () => {
      try {
        const response = await fetch('/api/hr/evaluations');
        const data = await response.json();
        setEvaluations(data);
      } catch (error) {
        console.error('Failed to fetch evaluations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvaluations();
  }, []);

  const filteredEvaluations = evaluations.filter(evaluation => {
    const matchesSearch =
      evaluation.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      evaluation.manager_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || evaluation.status === statusFilter;
    const matchesCycle = cycleFilter === 'all' || evaluation.cycle_name === cycleFilter;

    return matchesSearch && matchesStatus && matchesCycle;
  });

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'manager_review': return 'yellow';
      case 'committee_review': return 'blue';
      default: return 'gray';
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="All Evaluations"
        description="Monitor and manage all evaluations across the organization"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'HR Dashboard', href: '/hr' },
          { label: 'Evaluations', href: '/hr/evaluations' },
        ]}
      />

      {/* Filters */}
      <Card className="p-6">
        <div className="grid md:grid-cols-3 gap-4">
          <Input
            label="Search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by employee or manager..."
          />

          <Select
            label="Status"
            value={statusFilter}
            onChange={(value) => setStatusFilter(String(value))}
            options={[
              { value: 'all', label: 'All Statuses' },
              { value: 'peer_selection', label: 'Peer Selection' },
              { value: 'self_evaluation', label: 'Self Evaluation' },
              { value: 'manager_review', label: 'Manager Review' },
              { value: 'committee_review', label: 'Committee Review' },
              { value: 'completed', label: 'Completed' },
            ]}
          />

          <Select
            label="Cycle"
            value={cycleFilter}
            onChange={(value) => setCycleFilter(String(value))}
            options={[
              { value: 'all', label: 'All Cycles' },
              { value: 'Q4 2024', label: 'Q4 2024' },
              { value: 'Q3 2024', label: 'Q3 2024' },
            ]}
          />
        </div>

        <div className="mt-4 text-sm text-gray-600">
          Showing {filteredEvaluations.length} of {evaluations.length} evaluations
        </div>
      </Card>

      {/* Evaluations Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Manager
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cycle
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rating
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Updated
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEvaluations.map((evaluation) => (
                <tr key={evaluation.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{evaluation.employee_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-gray-700">{evaluation.manager_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-gray-700">{evaluation.cycle_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant={getStatusVariant(evaluation.status)}>
                      {evaluation.status.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-blue-600">
                      {evaluation.overall_rating
                        ? `${evaluation.overall_rating.toFixed(1)}/5`
                        : '—'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-600">
                      {new Date(evaluation.last_updated).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/hr/evaluations/${evaluation.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      View →
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
