/**
 * Utility Functions
 * Common utility functions used throughout the application
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { EvaluationPhase, EvaluationState } from '@/types/evaluation';

/**
 * Merge Tailwind CSS classes
 * Combines clsx and tailwind-merge for optimal class merging
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// ==================== Date & Time ====================

/**
 * Format date to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return 'just now';
  }
  if (diffMinutes < 60) {
    return `${diffMinutes} ${diffMinutes === 1 ? 'minute' : 'minutes'} ago`;
  }
  if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
  }
  if (diffDays < 7) {
    return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
  }
  if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} ${weeks === 1 ? 'week' : 'weeks'} ago`;
  }
  if (diffDays < 365) {
    const months = Math.floor(diffDays / 30);
    return `${months} ${months === 1 ? 'month' : 'months'} ago`;
  }
  const years = Math.floor(diffDays / 365);
  return `${years} ${years === 1 ? 'year' : 'years'} ago`;
}

/**
 * Format date to readable string
 */
export function formatDate(date: string | Date, includeTime = false): string {
  const d = new Date(date);
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };

  if (includeTime) {
    options.hour = '2-digit';
    options.minute = '2-digit';
  }

  return d.toLocaleDateString('en-US', options);
}

/**
 * Format duration in milliseconds to human readable
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }

  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

// ==================== Numbers ====================

/**
 * Format number with thousands separator
 */
export function formatNumber(num: number, decimals = 0): string {
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Format percentage
 */
export function formatPercentage(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Clamp number between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Round to specified decimal places
 */
export function round(value: number, decimals = 2): number {
  const multiplier = Math.pow(10, decimals);
  return Math.round(value * multiplier) / multiplier;
}

// ==================== Strings ====================

/**
 * Truncate string to specified length
 */
export function truncate(str: string, length: number, suffix = '...'): string {
  if (str.length <= length) {
    return str;
  }
  return str.slice(0, length - suffix.length) + suffix;
}

/**
 * Capitalize first letter
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert string to title case
 */
export function titleCase(str: string): string {
  return str
    .split(' ')
    .map((word) => capitalize(word.toLowerCase()))
    .join(' ');
}

/**
 * Convert snake_case to Title Case
 */
export function snakeToTitle(str: string): string {
  return str
    .split('_')
    .map((word) => capitalize(word))
    .join(' ');
}

/**
 * Generate random ID
 */
export function generateId(prefix = ''): string {
  const random = Math.random().toString(36).substring(2, 15);
  const timestamp = Date.now().toString(36);
  return prefix ? `${prefix}_${timestamp}${random}` : `${timestamp}${random}`;
}

// ==================== Arrays ====================

/**
 * Group array by key
 */
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce((result, item) => {
    const groupKey = String(item[key]);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey]!.push(item);
    return result;
  }, {} as Record<string, T[]>);
}

/**
 * Remove duplicates from array
 */
export function unique<T>(array: T[]): T[] {
  return [...new Set(array)];
}

/**
 * Chunk array into smaller arrays
 */
export function chunk<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

// ==================== Objects ====================

/**
 * Deep clone object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj)) as T;
}

/**
 * Check if object is empty
 */
export function isEmpty(obj: Record<string, unknown>): boolean {
  return Object.keys(obj).length === 0;
}

/**
 * Pick specific keys from object
 */
export function pick<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  const result = {} as Pick<T, K>;
  keys.forEach((key) => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
}

/**
 * Omit specific keys from object
 */
export function omit<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj };
  keys.forEach((key) => {
    delete result[key];
  });
  return result as Omit<T, K>;
}

// ==================== Evaluation Helpers ====================

/**
 * Get color for evaluation phase
 */
export function getPhaseColor(phase: EvaluationPhase): string {
  const colors: Record<EvaluationPhase, string> = {
    [EvaluationPhase.INTAKE]: 'blue',
    [EvaluationPhase.RATING]: 'purple',
    [EvaluationPhase.ANALYSIS]: 'teal',
    [EvaluationPhase.SYNTHESIS]: 'amber',
    [EvaluationPhase.COMPLETE]: 'green',
    [EvaluationPhase.FAILED]: 'red',
  };
  return colors[phase];
}

/**
 * Get color for evaluation state
 */
export function getStateColor(state: EvaluationState): string {
  const colors: Record<EvaluationState, string> = {
    [EvaluationState.PENDING]: 'gray',
    [EvaluationState.IN_PROGRESS]: 'blue',
    [EvaluationState.WAITING]: 'yellow',
    [EvaluationState.PROCESSING]: 'purple',
    [EvaluationState.COMPLETED]: 'green',
    [EvaluationState.FAILED]: 'red',
    [EvaluationState.CANCELLED]: 'orange',
  };
  return colors[state];
}

/**
 * Get score color based on value (0-10)
 */
export function getScoreColor(score: number): string {
  if (score >= 8) {
    return 'green';
  }
  if (score >= 6) {
    return 'yellow';
  }
  if (score >= 4) {
    return 'orange';
  }
  return 'red';
}

/**
 * Get confidence level label
 */
export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.9) {
    return 'Very High';
  }
  if (confidence >= 0.7) {
    return 'High';
  }
  if (confidence >= 0.5) {
    return 'Medium';
  }
  if (confidence >= 0.3) {
    return 'Low';
  }
  return 'Very Low';
}

// ==================== Async Helpers ====================

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Throttle function
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// ==================== File Size ====================

/**
 * Format bytes to human readable size
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) {
    return '0 Bytes';
  }

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}
