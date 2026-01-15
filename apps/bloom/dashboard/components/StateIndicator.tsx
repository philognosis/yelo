'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Circle } from 'lucide-react';

export interface StateIndicatorProps {
  state: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  animated?: boolean;
}

// State color mapping based on common evaluation phases
const stateColors: Record<string, { bg: string; text: string; border: string }> = {
  // Peer selection
  'Peer Selection': { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-300' },
  'peer_selection': { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-300' },

  // Self review
  'Self Review': { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
  'self_review': { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },

  // Peer review
  'Peer Review': { bg: 'bg-indigo-100', text: 'text-indigo-700', border: 'border-indigo-300' },
  'peer_review': { bg: 'bg-indigo-100', text: 'text-indigo-700', border: 'border-indigo-300' },

  // Manager review
  'Manager Review': { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-300' },
  'manager_review': { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-300' },

  // Calibration
  'Calibration': { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },
  'calibration': { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },

  // Delivery
  'Delivery': { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },
  'delivery': { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },

  // Acknowledgment
  'Acknowledgment': { bg: 'bg-teal-100', text: 'text-teal-700', border: 'border-teal-300' },
  'acknowledgment': { bg: 'bg-teal-100', text: 'text-teal-700', border: 'border-teal-300' },

  // Default
  'default': { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-300' },
};

const sizes = {
  sm: {
    dot: 'h-2 w-2',
    text: 'text-xs',
    padding: 'px-2 py-0.5',
  },
  md: {
    dot: 'h-2.5 w-2.5',
    text: 'text-sm',
    padding: 'px-2.5 py-1',
  },
  lg: {
    dot: 'h-3 w-3',
    text: 'text-base',
    padding: 'px-3 py-1.5',
  },
};

export default function StateIndicator({
  state,
  size = 'md',
  showLabel = true,
  animated = true,
}: StateIndicatorProps) {
  // Get color configuration for the state
  const colors = stateColors[state] || stateColors['default'];
  const sizeConfig = sizes[size];

  // Format state label (convert snake_case to Title Case)
  const formatLabel = (str: string) => {
    return str
      .replace(/_/g, ' ')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  if (!showLabel) {
    return (
      <div className="inline-flex items-center">
        <motion.div
          initial={animated ? { scale: 0 } : undefined}
          animate={animated ? { scale: 1 } : undefined}
          transition={{ duration: 0.2 }}
          className="relative"
        >
          <Circle
            className={`${sizeConfig.dot} ${colors.text} fill-current`}
            aria-label={formatLabel(state)}
          />
          {animated && (
            <motion.div
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.8, 0, 0.8],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className={`absolute inset-0 rounded-full ${colors.bg}`}
            />
          )}
        </motion.div>
      </div>
    );
  }

  return (
    <motion.div
      initial={animated ? { opacity: 0, scale: 0.9 } : undefined}
      animate={animated ? { opacity: 1, scale: 1 } : undefined}
      transition={{ duration: 0.2 }}
      className={`inline-flex items-center space-x-1.5 rounded-full border ${colors.bg} ${colors.border} ${sizeConfig.padding}`}
    >
      <div className="relative">
        <Circle className={`${sizeConfig.dot} ${colors.text} fill-current`} aria-hidden="true" />
        {animated && (
          <motion.div
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.8, 0, 0.8],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className={`absolute inset-0 rounded-full ${colors.bg}`}
          />
        )}
      </div>
      <span className={`font-medium ${colors.text} ${sizeConfig.text}`}>
        {formatLabel(state)}
      </span>
    </motion.div>
  );
}
