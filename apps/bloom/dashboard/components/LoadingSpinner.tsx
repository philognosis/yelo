'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'spinner' | 'dots' | 'pulse';
  text?: string;
  fullScreen?: boolean;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
  xl: 'h-16 w-16',
};

const dotSizes = {
  sm: 'h-1.5 w-1.5',
  md: 'h-2.5 w-2.5',
  lg: 'h-3.5 w-3.5',
  xl: 'h-4 w-4',
};

export default function LoadingSpinner({
  size = 'md',
  variant = 'spinner',
  text,
  fullScreen = false,
}: LoadingSpinnerProps) {
  const renderSpinner = () => {
    switch (variant) {
      case 'spinner':
        return (
          <Loader2
            className={`${sizeClasses[size]} animate-spin text-blue-600`}
            aria-hidden="true"
          />
        );

      case 'dots':
        return (
          <div className="flex space-x-2">
            {[0, 1, 2].map((index) => (
              <motion.div
                key={index}
                className={`${dotSizes[size]} rounded-full bg-blue-600`}
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  delay: index * 0.2,
                }}
                aria-hidden="true"
              />
            ))}
          </div>
        );

      case 'pulse':
        return (
          <motion.div
            className={`${sizeClasses[size]} rounded-full bg-blue-600`}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            aria-hidden="true"
          />
        );

      default:
        return null;
    }
  };

  const content = (
    <div className="flex flex-col items-center justify-center space-y-3">
      {renderSpinner()}
      {text && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-sm text-gray-600"
        >
          {text}
        </motion.p>
      )}
      <span className="sr-only">Loading...</span>
    </div>
  );

  if (fullScreen) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm"
        role="status"
        aria-live="polite"
      >
        {content}
      </motion.div>
    );
  }

  return (
    <div className="flex items-center justify-center p-4" role="status" aria-live="polite">
      {content}
    </div>
  );
}
