'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  MessageSquare,
  UserCheck,
  Clock,
  CheckCircle,
  AlertCircle,
  Info,
  LucideIcon,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export interface Activity {
  id: string;
  type: 'evaluation' | 'feedback' | 'approval' | 'reminder' | 'completion' | 'alert' | 'info';
  title: string;
  description?: string;
  timestamp: Date | string;
  user?: {
    name: string;
    avatar?: string;
  };
  link?: string;
}

export interface ActivityFeedProps {
  activities: Activity[];
  maxItems?: number;
  showTimestamps?: boolean;
  isLoading?: boolean;
  emptyMessage?: string;
}

const activityConfig: Record<
  Activity['type'],
  { icon: LucideIcon; color: string; bgColor: string }
> = {
  evaluation: {
    icon: FileText,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  feedback: {
    icon: MessageSquare,
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  approval: {
    icon: UserCheck,
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  reminder: {
    icon: Clock,
    color: 'text-amber-600',
    bgColor: 'bg-amber-100',
  },
  completion: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  alert: {
    icon: AlertCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
  info: {
    icon: Info,
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
  },
};

export default function ActivityFeed({
  activities,
  maxItems,
  showTimestamps = true,
  isLoading = false,
  emptyMessage = 'No recent activity',
}: ActivityFeedProps) {
  const displayedActivities = maxItems
    ? activities.slice(0, maxItems)
    : activities;

  const formatTime = (timestamp: Date | string) => {
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return formatDistanceToNow(date, { addSuffix: true });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex animate-pulse space-x-3">
            <div className="h-10 w-10 rounded-full bg-gray-200" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-3/4 rounded bg-gray-200" />
              <div className="h-3 w-1/2 rounded bg-gray-200" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (displayedActivities.length === 0) {
    return (
      <div className="py-12 text-center">
        <Clock className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
        <p className="mt-2 text-sm text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8" role="list">
        <AnimatePresence mode="popLayout">
          {displayedActivities.map((activity, index) => {
            const config = activityConfig[activity.type];
            const Icon = config.icon;
            const isLast = index === displayedActivities.length - 1;

            const content = (
              <motion.li
                key={activity.id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
              >
                <div className="relative pb-8">
                  {!isLast && (
                    <span
                      className="absolute left-5 top-5 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  )}
                  <div className="relative flex items-start space-x-3">
                    {/* Icon */}
                    <div className="relative">
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-full ${config.bgColor}`}
                      >
                        <Icon
                          className={`h-5 w-5 ${config.color}`}
                          aria-hidden="true"
                        />
                      </div>
                    </div>

                    {/* Content */}
                    <div className="min-w-0 flex-1">
                      <div>
                        <div className="text-sm">
                          {activity.user && (
                            <span className="font-medium text-gray-900">
                              {activity.user.name}
                            </span>
                          )}
                          <span className={activity.user ? 'ml-1' : ''}>
                            {activity.title}
                          </span>
                        </div>
                        {showTimestamps && (
                          <p className="mt-0.5 text-xs text-gray-500">
                            {formatTime(activity.timestamp)}
                          </p>
                        )}
                      </div>
                      {activity.description && (
                        <div className="mt-2 text-sm text-gray-600">
                          <p>{activity.description}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.li>
            );

            if (activity.link) {
              return (
                <a
                  key={activity.id}
                  href={activity.link}
                  className="block rounded-lg transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  {content}
                </a>
              );
            }

            return content;
          })}
        </AnimatePresence>
      </ul>
    </div>
  );
}
