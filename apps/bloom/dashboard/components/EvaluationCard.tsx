'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Calendar, User, Clock, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import Badge from './Badge';
import StateIndicator from './StateIndicator';

export interface EvaluationCardProps {
  id: string;
  title: string;
  period: string;
  dueDate: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'overdue';
  currentPhase: string;
  evaluator?: string;
  completionPercentage?: number;
  priority?: 'low' | 'medium' | 'high';
  onClick?: () => void;
}

const statusConfig = {
  not_started: { label: 'Not Started', variant: 'gray' as const },
  in_progress: { label: 'In Progress', variant: 'blue' as const },
  completed: { label: 'Completed', variant: 'green' as const },
  overdue: { label: 'Overdue', variant: 'red' as const },
};

const priorityConfig = {
  low: { color: 'bg-gray-200', textColor: 'text-gray-700' },
  medium: { color: 'bg-yellow-200', textColor: 'text-yellow-700' },
  high: { color: 'bg-red-200', textColor: 'text-red-700' },
};

export default function EvaluationCard({
  id,
  title,
  period,
  dueDate,
  status,
  currentPhase,
  evaluator,
  completionPercentage = 0,
  priority,
  onClick,
}: EvaluationCardProps) {
  const statusInfo = statusConfig[status];
  const priorityInfo = priority ? priorityConfig[priority] : null;

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
      className="group relative"
    >
      <Link
        href={`/evaluations/${id}`}
        onClick={handleClick}
        className="block rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        {/* Priority indicator */}
        {priorityInfo && (
          <div
            className={`absolute right-4 top-4 h-2 w-2 rounded-full ${priorityInfo.color}`}
            aria-label={`${priority} priority`}
          />
        )}

        {/* Header */}
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
            {title}
          </h3>
          <p className="mt-1 text-sm text-gray-500">{period}</p>
        </div>

        {/* Status and Phase */}
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
          <StateIndicator state={currentPhase} size="sm" />
        </div>

        {/* Details */}
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center">
            <Calendar className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>Due: {dueDate}</span>
          </div>
          {evaluator && (
            <div className="flex items-center">
              <User className="mr-2 h-4 w-4" aria-hidden="true" />
              <span>{evaluator}</span>
            </div>
          )}
          <div className="flex items-center">
            <Clock className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>{currentPhase}</span>
          </div>
        </div>

        {/* Progress bar */}
        {status === 'in_progress' && completionPercentage > 0 && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>Progress</span>
              <span>{completionPercentage}%</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-gray-200">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${completionPercentage}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
              />
            </div>
          </div>
        )}

        {/* Arrow indicator */}
        <div className="absolute bottom-6 right-6 text-gray-400 transition-transform group-hover:translate-x-1">
          <ChevronRight className="h-5 w-5" aria-hidden="true" />
        </div>
      </Link>
    </motion.div>
  );
}
