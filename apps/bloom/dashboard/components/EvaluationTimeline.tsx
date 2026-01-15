'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Check, Circle, Clock } from 'lucide-react';

export interface TimelinePhase {
  phase: string;
  status: 'completed' | 'current' | 'upcoming';
  date?: string;
  description?: string;
}

export interface EvaluationTimelineProps {
  phases: TimelinePhase[];
  orientation?: 'vertical' | 'horizontal';
}

const statusConfig = {
  completed: {
    icon: Check,
    color: 'bg-green-500',
    borderColor: 'border-green-500',
    textColor: 'text-green-700',
    lineColor: 'bg-green-500',
  },
  current: {
    icon: Clock,
    color: 'bg-blue-500',
    borderColor: 'border-blue-500',
    textColor: 'text-blue-700',
    lineColor: 'bg-gray-300',
  },
  upcoming: {
    icon: Circle,
    color: 'bg-gray-300',
    borderColor: 'border-gray-300',
    textColor: 'text-gray-500',
    lineColor: 'bg-gray-300',
  },
};

export default function EvaluationTimeline({
  phases,
  orientation = 'vertical',
}: EvaluationTimelineProps) {
  if (orientation === 'horizontal') {
    return (
      <div className="overflow-x-auto pb-4">
        <div className="flex min-w-max items-start space-x-4">
          {phases.map((phase, index) => {
            const config = statusConfig[phase.status];
            const Icon = config.icon;
            const isLast = index === phases.length - 1;

            return (
              <div key={index} className="flex items-center">
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex flex-col items-center"
                >
                  {/* Icon */}
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-full ${config.color} text-white shadow-md`}
                    aria-label={`${phase.phase} - ${phase.status}`}
                  >
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </div>

                  {/* Content */}
                  <div className="mt-3 text-center" style={{ maxWidth: '150px' }}>
                    <p className={`text-sm font-semibold ${config.textColor}`}>
                      {phase.phase}
                    </p>
                    {phase.date && (
                      <p className="mt-1 text-xs text-gray-500">{phase.date}</p>
                    )}
                    {phase.description && (
                      <p className="mt-1 text-xs text-gray-600">{phase.description}</p>
                    )}
                  </div>
                </motion.div>

                {/* Connecting line */}
                {!isLast && (
                  <div
                    className={`mx-2 h-0.5 w-16 ${config.lineColor}`}
                    aria-hidden="true"
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Vertical orientation
  return (
    <div className="space-y-0">
      {phases.map((phase, index) => {
        const config = statusConfig[phase.status];
        const Icon = config.icon;
        const isLast = index === phases.length - 1;

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="relative flex"
          >
            {/* Timeline line */}
            {!isLast && (
              <div
                className={`absolute left-5 top-10 h-full w-0.5 ${config.lineColor}`}
                aria-hidden="true"
              />
            )}

            {/* Icon */}
            <div className="relative z-10 mr-4 flex-shrink-0">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full ${config.color} text-white shadow-md`}
                aria-label={`${phase.phase} - ${phase.status}`}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
            </div>

            {/* Content */}
            <div className={`flex-1 pb-8 ${isLast ? 'pb-0' : ''}`}>
              <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className={`font-semibold ${config.textColor}`}>
                      {phase.phase}
                    </h4>
                    {phase.description && (
                      <p className="mt-1 text-sm text-gray-600">{phase.description}</p>
                    )}
                  </div>
                  {phase.date && (
                    <span className="ml-4 flex-shrink-0 text-xs text-gray-500">
                      {phase.date}
                    </span>
                  )}
                </div>

                {/* Status indicator */}
                <div className="mt-2">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      phase.status === 'completed'
                        ? 'bg-green-100 text-green-800'
                        : phase.status === 'current'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {phase.status === 'completed'
                      ? 'Completed'
                      : phase.status === 'current'
                      ? 'In Progress'
                      : 'Upcoming'}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
