'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, User, Clock, FileText, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import Badge from './Badge';
import StateIndicator from './StateIndicator';
import EvaluationTimeline from './EvaluationTimeline';
import Card from './Card';

export interface EvaluationDetailProps {
  id: string;
  title: string;
  period: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'overdue';
  currentPhase: string;
  evaluator: {
    name: string;
    role: string;
    avatar?: string;
  };
  employee: {
    name: string;
    role: string;
    avatar?: string;
  };
  dueDate: string;
  createdDate: string;
  description?: string;
  objectives?: Array<{ id: string; title: string; completed: boolean }>;
  feedback?: Array<{ id: string; author: string; text: string; date: string }>;
  timeline?: Array<{
    phase: string;
    status: 'completed' | 'current' | 'upcoming';
    date?: string;
  }>;
  isLoading?: boolean;
}

const statusConfig = {
  not_started: { label: 'Not Started', variant: 'gray' as const },
  in_progress: { label: 'In Progress', variant: 'blue' as const },
  completed: { label: 'Completed', variant: 'green' as const },
  overdue: { label: 'Overdue', variant: 'red' as const },
};

export default function EvaluationDetail({
  id,
  title,
  period,
  status,
  currentPhase,
  evaluator,
  employee,
  dueDate,
  createdDate,
  description,
  objectives = [],
  feedback = [],
  timeline = [],
  isLoading = false,
}: EvaluationDetailProps) {
  const [showObjectives, setShowObjectives] = useState(true);
  const [showFeedback, setShowFeedback] = useState(true);

  const statusInfo = statusConfig[status];

  if (isLoading) {
    return (
      <Card>
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-3/4 rounded bg-gray-200" />
          <div className="h-4 w-1/2 rounded bg-gray-200" />
          <div className="space-y-2">
            <div className="h-4 w-full rounded bg-gray-200" />
            <div className="h-4 w-5/6 rounded bg-gray-200" />
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
              <p className="mt-1 text-sm text-gray-500">{period}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
              <StateIndicator state={currentPhase} />
            </div>
          </div>

          {description && (
            <p className="mb-6 text-gray-700">{description}</p>
          )}

          {/* Participants */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex items-center space-x-3 rounded-lg bg-gray-50 p-4">
              {employee.avatar ? (
                <img
                  src={employee.avatar}
                  alt={employee.name}
                  className="h-10 w-10 rounded-full object-cover"
                />
              ) : (
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
                  <span className="text-sm font-medium text-white">
                    {employee.name.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-gray-900">{employee.name}</p>
                <p className="text-xs text-gray-500">Employee • {employee.role}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3 rounded-lg bg-gray-50 p-4">
              {evaluator.avatar ? (
                <img
                  src={evaluator.avatar}
                  alt={evaluator.name}
                  className="h-10 w-10 rounded-full object-cover"
                />
              ) : (
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-600">
                  <span className="text-sm font-medium text-white">
                    {evaluator.name.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-gray-900">{evaluator.name}</p>
                <p className="text-xs text-gray-500">Evaluator • {evaluator.role}</p>
              </div>
            </div>
          </div>

          {/* Dates */}
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Calendar className="h-4 w-4" aria-hidden="true" />
              <div>
                <p className="text-xs text-gray-500">Created</p>
                <p className="font-medium">{createdDate}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="h-4 w-4" aria-hidden="true" />
              <div>
                <p className="text-xs text-gray-500">Due Date</p>
                <p className="font-medium">{dueDate}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <User className="h-4 w-4" aria-hidden="true" />
              <div>
                <p className="text-xs text-gray-500">Current Phase</p>
                <p className="font-medium">{currentPhase}</p>
              </div>
            </div>
          </div>
        </motion.div>
      </Card>

      {/* Timeline */}
      {timeline.length > 0 && (
        <Card>
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Timeline</h3>
          <EvaluationTimeline phases={timeline} />
        </Card>
      )}

      {/* Objectives */}
      {objectives.length > 0 && (
        <Card>
          <button
            onClick={() => setShowObjectives(!showObjectives)}
            className="flex w-full items-center justify-between text-left"
            aria-expanded={showObjectives}
          >
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-gray-400" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-gray-900">
                Objectives ({objectives.length})
              </h3>
            </div>
            {showObjectives ? (
              <ChevronUp className="h-5 w-5 text-gray-400" aria-hidden="true" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-400" aria-hidden="true" />
            )}
          </button>

          <AnimatePresence>
            {showObjectives && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="mt-4 space-y-2"
              >
                {objectives.map((objective) => (
                  <div
                    key={objective.id}
                    className="flex items-start space-x-3 rounded-lg border border-gray-200 p-3"
                  >
                    <input
                      type="checkbox"
                      checked={objective.completed}
                      readOnly
                      className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      aria-label={`${objective.title} - ${objective.completed ? 'completed' : 'not completed'}`}
                    />
                    <p
                      className={`flex-1 text-sm ${
                        objective.completed ? 'text-gray-500 line-through' : 'text-gray-900'
                      }`}
                    >
                      {objective.title}
                    </p>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      )}

      {/* Feedback */}
      {feedback.length > 0 && (
        <Card>
          <button
            onClick={() => setShowFeedback(!showFeedback)}
            className="flex w-full items-center justify-between text-left"
            aria-expanded={showFeedback}
          >
            <div className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5 text-gray-400" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-gray-900">
                Feedback ({feedback.length})
              </h3>
            </div>
            {showFeedback ? (
              <ChevronUp className="h-5 w-5 text-gray-400" aria-hidden="true" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-400" aria-hidden="true" />
            )}
          </button>

          <AnimatePresence>
            {showFeedback && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="mt-4 space-y-4"
              >
                {feedback.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-lg border border-gray-200 bg-gray-50 p-4"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900">{item.author}</p>
                      <p className="text-xs text-gray-500">{item.date}</p>
                    </div>
                    <p className="text-sm text-gray-700">{item.text}</p>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      )}
    </div>
  );
}
