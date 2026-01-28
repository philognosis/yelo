'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Badge from '@/components/Badge';
import LoadingSpinner from '@/components/LoadingSpinner';
import {
  ControlRoomData,
  EvaluationOverview,
  EvaluationPhase,
  EvaluationState,
  DeadlineStatus,
  ActivityEvent,
  DeadlineAlert,
} from '@/types/admin';
import { getControlRoomData } from '@/lib/admin-api';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Users,
  TrendingUp,
  RefreshCw,
  Filter,
  Download,
} from 'lucide-react';

export default function ControlRoomPage() {
  const router = useRouter();
  const [data, setData] = useState<ControlRoomData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [selectedPhase, setSelectedPhase] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Load data
  const loadData = async () => {
    try {
      const controlRoomData = await getControlRoomData();
      setData(controlRoomData);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load control room data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadData();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const { health, evaluations, recent_activity, deadline_alerts, phase_distribution, department_stats } = data;

  // Filter evaluations
  const filteredEvaluations = evaluations.filter((evaluation) => {
    const matchesPhase = selectedPhase === 'all' || evaluation.current_phase === selectedPhase;
    const matchesSearch = !searchTerm ||
      evaluation.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      evaluation.employee_department.toLowerCase().includes(searchTerm.toLowerCase()) ||
      evaluation.manager_name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesPhase && matchesSearch;
  });

  const getPhaseColor = (phase: EvaluationPhase): 'blue' | 'yellow' | 'purple' | 'green' | 'gray' => {
    switch (phase) {
      case EvaluationPhase.CONTEXT_PEER_SELECTION: return 'blue';
      case EvaluationPhase.DATA_GATHERING: return 'yellow';
      case EvaluationPhase.MANAGER_EVALUATION: return 'purple';
      case EvaluationPhase.CALIBRATION: return 'pink';
      case EvaluationPhase.RELEASE_DISCUSSION: return 'indigo';
      case EvaluationPhase.COMPLETED: return 'green';
      default: return 'gray';
    }
  };

  const getDeadlineStatusColor = (status: DeadlineStatus): 'red' | 'yellow' | 'blue' | 'green' | 'gray' => {
    switch (status) {
      case DeadlineStatus.OVERDUE: return 'red';
      case DeadlineStatus.DUE_TODAY: return 'yellow';
      case DeadlineStatus.APPROACHING: return 'yellow';
      case DeadlineStatus.UPCOMING: return 'blue';
      case DeadlineStatus.COMPLETED: return 'green';
      default: return 'gray';
    }
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-[1800px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">HR Control Room</h1>
          <p className="text-sm text-gray-500 mt-1">
            Live view of all evaluations • Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button variant="secondary" size="sm" onClick={loadData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Now
          </Button>
          <Button variant="ghost" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* System Health Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Total Active */}
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Active Evaluations</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{health.active_evaluations}</p>
              <p className="text-xs text-gray-500 mt-1">
                {health.total_evaluations} total
              </p>
            </div>
            <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </Card>

        {/* Completed */}
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Completed</p>
              <p className="text-3xl font-bold text-green-600 mt-1">{health.completed_evaluations}</p>
              <p className="text-xs text-gray-500 mt-1">
                {((health.completed_evaluations / health.total_evaluations) * 100).toFixed(0)}% completion rate
              </p>
            </div>
            <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>

        {/* Alerts */}
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Needs Attention</p>
              <p className="text-3xl font-bold text-red-600 mt-1">{health.overdue_count}</p>
              <p className="text-xs text-gray-500 mt-1">
                {health.approaching_deadline_count} approaching deadlines
              </p>
            </div>
            <div className="h-12 w-12 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
          </div>
        </Card>

        {/* Performance */}
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">On Track</p>
              <p className="text-3xl font-bold text-indigo-600 mt-1">{health.on_track_percentage}%</p>
              <p className="text-xs text-gray-500 mt-1">
                Avg {health.avg_completion_time_days}d to complete
              </p>
            </div>
            <div className="h-12 w-12 bg-indigo-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="h-6 w-6 text-indigo-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Pipeline Visualization - 2/3 width */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Evaluation Pipeline</h2>
            <div className="space-y-3">
              {phase_distribution.map((phase) => (
                <div key={phase.phase} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <Badge variant={getPhaseColor(phase.phase)}>
                        {phase.phase.replace(/_/g, ' ').toUpperCase()}
                      </Badge>
                      <span className="text-gray-600">{phase.count} evaluations</span>
                    </div>
                    <span className="text-gray-500">{phase.percentage.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all duration-500 ${
                        phase.phase === EvaluationPhase.COMPLETED ? 'bg-green-500' :
                        phase.phase === EvaluationPhase.MANAGER_EVALUATION ? 'bg-purple-500' :
                        phase.phase === EvaluationPhase.DATA_GATHERING ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`}
                      style={{ width: `${phase.percentage}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500">
                    Avg time: {phase.avg_time_in_phase_days.toFixed(1)} days
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Real-time Activity Feed - 1/3 width */}
        <div className="lg:col-span-1">
          <Card className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="h-5 w-5 text-gray-600" />
              <h2 className="text-lg font-semibold">Live Activity</h2>
            </div>
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {recent_activity.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">No recent activity</p>
              ) : (
                recent_activity.map((event) => (
                  <div key={event.id} className="flex gap-3 pb-3 border-b border-gray-100 last:border-0">
                    <div className="flex-shrink-0 mt-0.5">
                      <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 font-medium">
                        {event.employee_name}
                      </p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        {event.description}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(event.timestamp).toLocaleTimeString()} • {event.actor_type}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Deadline Alerts */}
      {deadline_alerts.length > 0 && (
        <Card className="p-6 mb-6 border-l-4 border-l-red-500">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <h2 className="text-lg font-semibold text-red-900">Deadline Alerts</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {deadline_alerts.slice(0, 6).map((alert) => (
              <div key={alert.id} className="p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{alert.employee_name}</p>
                    <p className="text-xs text-gray-600 mt-1">{alert.deadline_type}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Clock className="h-3 w-3 text-red-600" />
                      <span className="text-xs font-medium text-red-600">
                        {alert.status === DeadlineStatus.OVERDUE
                          ? `${Math.abs(alert.days_remaining)} days overdue`
                          : `Due in ${alert.days_remaining} days`}
                      </span>
                    </div>
                  </div>
                  <Badge variant={getDeadlineStatusColor(alert.status)} size="sm">
                    {alert.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
          {deadline_alerts.length > 6 && (
            <p className="text-sm text-gray-500 mt-3">
              + {deadline_alerts.length - 6} more alerts
            </p>
          )}
        </Card>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search by employee, department, or manager..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={selectedPhase === 'all' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setSelectedPhase('all')}
          >
            All ({evaluations.length})
          </Button>
          {Object.values(EvaluationPhase).filter(p => p !== EvaluationPhase.CANCELLED).map((phase) => {
            const count = evaluations.filter(e => e.current_phase === phase).length;
            return (
              <Button
                key={phase}
                variant={selectedPhase === phase ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setSelectedPhase(phase)}
              >
                {phase.replace(/_/g, ' ')} ({count})
              </Button>
            );
          })}
        </div>
      </div>

      {/* Evaluations Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Manager
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phase
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Activity
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEvaluations.map((evaluation) => (
                <tr key={evaluation.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{evaluation.employee_name}</div>
                      <div className="text-xs text-gray-500">{evaluation.employee_title}</div>
                      <div className="text-xs text-gray-400">{evaluation.employee_department}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{evaluation.manager_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant={getPhaseColor(evaluation.current_phase)}>
                      {evaluation.current_phase.replace(/_/g, ' ')}
                    </Badge>
                    <div className="text-xs text-gray-500 mt-1">
                      {evaluation.current_state.replace(/_/g, ' ')}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2 w-24">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${evaluation.completion_percentage}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600">{evaluation.completion_percentage}%</span>
                    </div>
                    <div className="flex gap-1 mt-2">
                      {evaluation.self_eval_complete && (
                        <CheckCircle2 className="h-3 w-3 text-green-600" title="Self-eval complete" />
                      )}
                      {evaluation.peer_feedback_count > 0 && (
                        <span className="text-xs text-gray-500" title="Peer feedback">
                          {evaluation.peer_feedback_count}/{evaluation.peer_feedback_total} peers
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {evaluation.is_overdue && (
                      <Badge variant="red" size="sm">
                        Overdue
                      </Badge>
                    )}
                    {evaluation.is_blocked && (
                      <Badge variant="yellow" size="sm">
                        Blocked
                      </Badge>
                    )}
                    {!evaluation.is_overdue && !evaluation.is_blocked && (
                      <Badge variant="green" size="sm">
                        On Track
                      </Badge>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(evaluation.last_activity_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push(`/hr/evaluations/${evaluation.id}`)}
                    >
                      View Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredEvaluations.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No evaluations found matching your filters</p>
          </div>
        )}
      </Card>
    </div>
  );
}
