'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Brain,
  Users,
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  Activity,
} from 'lucide-react';
import Badge from './Badge';
import Card from './Card';

export interface AgentStatus {
  agentId: string;
  agentType: 'orchestrator' | 'peer_selector' | 'feedback_analyzer' | 'draft_generator' | 'evidence_collector';
  status: 'idle' | 'processing' | 'completed' | 'error';
  currentTask?: string;
  progress?: number;
  startedAt?: Date | string;
  completedAt?: Date | string;
  error?: string;
}

export interface LiveStatusProps {
  agents: AgentStatus[];
  evaluationId?: string;
  showDetails?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onAgentClick?: (agentId: string) => void;
}

const agentTypeConfig = {
  orchestrator: {
    label: 'Orchestrator',
    icon: Brain,
    color: 'purple',
  },
  peer_selector: {
    label: 'Peer Selector',
    icon: Users,
    color: 'blue',
  },
  feedback_analyzer: {
    label: 'Feedback Analyzer',
    icon: FileText,
    color: 'green',
  },
  draft_generator: {
    label: 'Draft Generator',
    icon: Sparkles,
    color: 'indigo',
  },
  evidence_collector: {
    label: 'Evidence Collector',
    icon: Activity,
    color: 'yellow',
  },
} as const;

const statusConfig = {
  idle: {
    label: 'Idle',
    icon: Clock,
    variant: 'gray' as const,
  },
  processing: {
    label: 'Processing',
    icon: Activity,
    variant: 'blue' as const,
  },
  completed: {
    label: 'Completed',
    icon: CheckCircle,
    variant: 'green' as const,
  },
  error: {
    label: 'Error',
    icon: AlertCircle,
    variant: 'red' as const,
  },
};

export default function LiveStatus({
  agents,
  evaluationId,
  showDetails = true,
  autoRefresh = true,
  refreshInterval = 2000,
  onAgentClick,
}: LiveStatusProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setIsRefreshing(true);
      setLastUpdate(new Date());
      setTimeout(() => setIsRefreshing(false), 300);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const activeAgents = agents.filter((a) => a.status === 'processing').length;
  const completedAgents = agents.filter((a) => a.status === 'completed').length;
  const errorAgents = agents.filter((a) => a.status === 'error').length;

  return (
    <Card>
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sparkles className="h-5 w-5 text-purple-600" aria-hidden="true" />
          <h3 className="text-lg font-semibold text-gray-900">
            AI Agent Swarm Status
          </h3>
          {evaluationId && (
            <Badge variant="gray" size="sm">
              {evaluationId}
            </Badge>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <motion.div
            animate={{ rotate: isRefreshing ? 360 : 0 }}
            transition={{ duration: 0.5 }}
          >
            <Activity
              className={`h-4 w-4 ${
                activeAgents > 0 ? 'text-blue-600' : 'text-gray-400'
              }`}
              aria-hidden="true"
            />
          </motion.div>
          <span className="text-xs text-gray-500">
            Updated {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mb-4 grid grid-cols-4 gap-3">
        <div className="rounded-lg bg-gray-50 p-3 text-center">
          <p className="text-2xl font-bold text-gray-900">{agents.length}</p>
          <p className="text-xs text-gray-600">Total Agents</p>
        </div>
        <div className="rounded-lg bg-blue-50 p-3 text-center">
          <p className="text-2xl font-bold text-blue-600">{activeAgents}</p>
          <p className="text-xs text-blue-600">Active</p>
        </div>
        <div className="rounded-lg bg-green-50 p-3 text-center">
          <p className="text-2xl font-bold text-green-600">{completedAgents}</p>
          <p className="text-xs text-green-600">Completed</p>
        </div>
        <div className="rounded-lg bg-red-50 p-3 text-center">
          <p className="text-2xl font-bold text-red-600">{errorAgents}</p>
          <p className="text-xs text-red-600">Errors</p>
        </div>
      </div>

      {/* Agent List */}
      {showDetails && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Agent Details</h4>
          <AnimatePresence mode="popLayout">
            {agents.map((agent, index) => {
              const typeConfig = agentTypeConfig[agent.agentType];
              const statusInfo = statusConfig[agent.status];
              const TypeIcon = typeConfig.icon;
              const StatusIcon = statusInfo.icon;

              return (
                <motion.div
                  key={agent.agentId}
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => onAgentClick?.(agent.agentId)}
                  className={`rounded-lg border border-gray-200 bg-white p-3 ${
                    onAgentClick ? 'cursor-pointer transition-all hover:shadow-md' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    {/* Agent Info */}
                    <div className="flex items-start space-x-3">
                      <div
                        className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-${typeConfig.color}-100`}
                      >
                        <TypeIcon
                          className={`h-5 w-5 text-${typeConfig.color}-600`}
                          aria-hidden="true"
                        />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center space-x-2">
                          <p className="text-sm font-medium text-gray-900">
                            {typeConfig.label}
                          </p>
                          <Badge variant={statusInfo.variant} size="sm">
                            <StatusIcon className="mr-1 h-3 w-3" aria-hidden="true" />
                            {statusInfo.label}
                          </Badge>
                        </div>
                        {agent.currentTask && (
                          <p className="mt-1 text-xs text-gray-600">
                            {agent.currentTask}
                          </p>
                        )}
                        {agent.error && (
                          <p className="mt-1 text-xs text-red-600">{agent.error}</p>
                        )}
                      </div>
                    </div>

                    {/* Progress */}
                    {agent.progress !== undefined && agent.status === 'processing' && (
                      <div className="ml-4 flex-shrink-0">
                        <div className="text-right">
                          <span className="text-xs font-medium text-blue-600">
                            {agent.progress}%
                          </span>
                        </div>
                        <div className="mt-1 h-1.5 w-16 overflow-hidden rounded-full bg-gray-200">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${agent.progress}%` }}
                            transition={{ duration: 0.5 }}
                            className="h-full rounded-full bg-blue-600"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {/* Overall Progress */}
      {agents.length > 0 && (
        <div className="mt-4 rounded-lg bg-gray-50 p-3">
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="font-medium text-gray-700">Overall Progress</span>
            <span className="text-gray-600">
              {completedAgents} / {agents.length} agents completed
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-gray-200">
            <motion.div
              initial={{ width: 0 }}
              animate={{
                width: `${(completedAgents / agents.length) * 100}%`,
              }}
              transition={{ duration: 0.5 }}
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
            />
          </div>
        </div>
      )}
    </Card>
  );
}
