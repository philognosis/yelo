'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverable?: boolean;
  onClick?: () => void;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const paddingClasses = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export default function Card({
  children,
  className = '',
  hoverable = false,
  onClick,
  padding = 'md',
}: CardProps) {
  const isInteractive = hoverable || onClick;

  const Component = motion.div;

  return (
    <Component
      onClick={onClick}
      whileHover={isInteractive ? { y: -4 } : undefined}
      transition={{ duration: 0.2 }}
      className={`rounded-lg border border-gray-200 bg-white shadow-sm ${
        isInteractive ? 'cursor-pointer transition-shadow hover:shadow-md' : ''
      } ${paddingClasses[padding]} ${className}`}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
    >
      {children}
    </Component>
  );
}
