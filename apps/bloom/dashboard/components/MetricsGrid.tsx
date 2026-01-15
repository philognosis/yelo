'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  LucideIcon,
} from 'lucide-react';

export interface Metric {
  id: string;
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: LucideIcon;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'indigo';
  href?: string;
}

export interface MetricsGridProps {
  metrics: Metric[];
  isLoading?: boolean;
  columns?: 2 | 3 | 4;
}

const colorClasses = {
  blue: {
    bg: 'bg-blue-500',
    lightBg: 'bg-blue-50',
    text: 'text-blue-600',
    gradient: 'from-blue-500 to-blue-600',
  },
  green: {
    bg: 'bg-green-500',
    lightBg: 'bg-green-50',
    text: 'text-green-600',
    gradient: 'from-green-500 to-green-600',
  },
  yellow: {
    bg: 'bg-yellow-500',
    lightBg: 'bg-yellow-50',
    text: 'text-yellow-600',
    gradient: 'from-yellow-500 to-yellow-600',
  },
  red: {
    bg: 'bg-red-500',
    lightBg: 'bg-red-50',
    text: 'text-red-600',
    gradient: 'from-red-500 to-red-600',
  },
  purple: {
    bg: 'bg-purple-500',
    lightBg: 'bg-purple-50',
    text: 'text-purple-600',
    gradient: 'from-purple-500 to-purple-600',
  },
  indigo: {
    bg: 'bg-indigo-500',
    lightBg: 'bg-indigo-50',
    text: 'text-indigo-600',
    gradient: 'from-indigo-500 to-indigo-600',
  },
};

const gridColumns = {
  2: 'sm:grid-cols-2',
  3: 'sm:grid-cols-2 lg:grid-cols-3',
  4: 'sm:grid-cols-2 lg:grid-cols-4',
};

export default function MetricsGrid({
  metrics,
  isLoading = false,
  columns = 4,
}: MetricsGridProps) {
  if (isLoading) {
    return (
      <div className={`grid gap-4 ${gridColumns[columns]}`}>
        {[...Array(columns)].map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-lg border border-gray-200 bg-white p-6"
          >
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="h-4 w-24 rounded bg-gray-200" />
                <div className="h-8 w-16 rounded bg-gray-200" />
              </div>
              <div className="h-12 w-12 rounded-lg bg-gray-200" />
            </div>
            <div className="mt-4 h-3 w-20 rounded bg-gray-200" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`grid gap-4 ${gridColumns[columns]}`}>
      {metrics.map((metric, index) => {
        const Icon = metric.icon;
        const colors = colorClasses[metric.color];
        const hasChange = typeof metric.change === 'number';
        const isPositive = metric.change && metric.change > 0;
        const isNegative = metric.change && metric.change < 0;

        const card = (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -4 }}
            className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-600">{metric.title}</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">{metric.value}</p>
              </div>
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br ${colors.gradient}`}
              >
                <Icon className="h-6 w-6 text-white" aria-hidden="true" />
              </div>
            </div>

            {hasChange && (
              <div className="mt-4 flex items-center space-x-2">
                {isPositive ? (
                  <TrendingUp className="h-4 w-4 text-green-600" aria-hidden="true" />
                ) : isNegative ? (
                  <TrendingDown className="h-4 w-4 text-red-600" aria-hidden="true" />
                ) : (
                  <Minus className="h-4 w-4 text-gray-400" aria-hidden="true" />
                )}
                <span
                  className={`text-sm font-medium ${
                    isPositive
                      ? 'text-green-600'
                      : isNegative
                      ? 'text-red-600'
                      : 'text-gray-600'
                  }`}
                >
                  {isPositive && '+'}
                  {metric.change}%
                </span>
                {metric.changeLabel && (
                  <span className="text-sm text-gray-500">{metric.changeLabel}</span>
                )}
              </div>
            )}
          </motion.div>
        );

        if (metric.href) {
          return (
            <a
              key={metric.id}
              href={metric.href}
              className="block focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-lg"
            >
              {card}
            </a>
          );
        }

        return <div key={metric.id}>{card}</div>;
      })}
    </div>
  );
}
