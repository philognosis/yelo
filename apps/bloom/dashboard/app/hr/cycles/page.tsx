'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '../../../components/PageHeader';
import { Card } from '../../../components/Card';
import { Badge } from '../../../components/Badge';
import { Button } from '../../../components/Button';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { EmptyState } from '../../../components/EmptyState';
import Link from 'next/link';

interface EvaluationCycle {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'completed' | 'archived';
  start_date: string;
  end_date: string;
  participant_count: number;
  completion_rate: number;
  created_at: string;
}

export default function CyclesPage() {
  const [cycles, setCycles] = useState<EvaluationCycle[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');

  useEffect(() => {
    const fetchCycles = async () => {
      try {
        const response = await fetch('/api/hr/cycles');
        const data = await response.json();
        setCycles(data);
      } catch (error) {
        console.error('Failed to fetch cycles:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCycles();
  }, []);

  const filteredCycles = cycles.filter(cycle => {
    if (filter === 'all') return true;
    return cycle.status === filter;
  });

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'completed': return 'default';
      case 'draft': return 'warning';
      default: return 'default';
    }
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
        title="Evaluation Cycles"
        description="Manage performance evaluation cycles"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'HR Dashboard', href: '/hr' },
          { label: 'Cycles', href: '/hr/cycles' },
        ]}
        action={
          <Link href="/hr/cycles/new">
            <Button variant="primary">Create New Cycle</Button>
          </Link>
        }
      />

      {/* Filters */}
      <Card className="p-4">
        <div className="flex gap-3">
          <Button
            variant={filter === 'all' ? 'primary' : 'outline'}
            onClick={() => setFilter('all')}
          >
            All Cycles
          </Button>
          <Button
            variant={filter === 'active' ? 'primary' : 'outline'}
            onClick={() => setFilter('active')}
          >
            Active
          </Button>
          <Button
            variant={filter === 'completed' ? 'primary' : 'outline'}
            onClick={() => setFilter('completed')}
          >
            Completed
          </Button>
        </div>
      </Card>

      {/* Cycles List */}
      {filteredCycles.length === 0 ? (
        <EmptyState
          title="No cycles found"
          description="Create your first evaluation cycle to get started."
          action={
            <Link href="/hr/cycles/new">
              <Button variant="primary">Create Cycle</Button>
            </Link>
          }
        />
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {filteredCycles.map((cycle) => (
            <Link key={cycle.id} href={`/hr/cycles/${cycle.id}`}>
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold mb-2">{cycle.name}</h3>
                    <Badge variant={getStatusVariant(cycle.status)}>
                      {cycle.status.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">
                      {cycle.completion_rate}%
                    </div>
                    <div className="text-sm text-gray-600">Complete</div>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Start Date</span>
                    <span className="font-medium">
                      {new Date(cycle.start_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">End Date</span>
                    <span className="font-medium">
                      {new Date(cycle.end_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Participants</span>
                    <span className="font-medium">{cycle.participant_count}</span>
                  </div>
                </div>

                <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${cycle.completion_rate}%` }}
                  />
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
