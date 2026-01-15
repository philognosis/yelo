'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'gray' | 'red' | 'yellow' | 'green' | 'blue' | 'indigo' | 'purple' | 'pink';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  removable?: boolean;
  onRemove?: () => void;
  className?: string;
}

const variantClasses = {
  gray: 'bg-gray-100 text-gray-700 border-gray-300',
  red: 'bg-red-100 text-red-700 border-red-300',
  yellow: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  green: 'bg-green-100 text-green-700 border-green-300',
  blue: 'bg-blue-100 text-blue-700 border-blue-300',
  indigo: 'bg-indigo-100 text-indigo-700 border-indigo-300',
  purple: 'bg-purple-100 text-purple-700 border-purple-300',
  pink: 'bg-pink-100 text-pink-700 border-pink-300',
};

const dotColors = {
  gray: 'bg-gray-400',
  red: 'bg-red-400',
  yellow: 'bg-yellow-400',
  green: 'bg-green-400',
  blue: 'bg-blue-400',
  indigo: 'bg-indigo-400',
  purple: 'bg-purple-400',
  pink: 'bg-pink-400',
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-0.5 text-sm',
  lg: 'px-3 py-1 text-base',
};

export default function Badge({
  children,
  variant = 'gray',
  size = 'md',
  dot = false,
  removable = false,
  onRemove,
  className = '',
}: BadgeProps) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className={`inline-flex items-center rounded-full font-medium ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {dot && (
        <span
          className={`mr-1.5 h-2 w-2 rounded-full ${dotColors[variant]}`}
          aria-hidden="true"
        />
      )}
      {children}
      {removable && onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-1 inline-flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full hover:bg-black/10 focus:bg-black/10 focus:outline-none"
          aria-label="Remove"
        >
          <X className="h-3 w-3" aria-hidden="true" />
        </button>
      )}
    </motion.span>
  );
}
