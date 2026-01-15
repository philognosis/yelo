'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
  X,
  ChevronRight,
} from 'lucide-react';

export interface Alert {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  dismissible?: boolean;
  autoHideDuration?: number;
}

export interface AlertBannerProps {
  alerts: Alert[];
  onDismiss?: (alertId: string) => void;
  position?: 'top' | 'bottom';
  maxAlerts?: number;
}

const alertConfig = {
  success: {
    icon: CheckCircle,
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    iconColor: 'text-green-600',
  },
  error: {
    icon: AlertCircle,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
    iconColor: 'text-red-600',
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-800',
    iconColor: 'text-yellow-600',
  },
  info: {
    icon: Info,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-800',
    iconColor: 'text-blue-600',
  },
};

export default function AlertBanner({
  alerts,
  onDismiss,
  position = 'top',
  maxAlerts = 3,
}: AlertBannerProps) {
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());

  const handleDismiss = (alertId: string) => {
    setDismissedAlerts((prev) => new Set(prev).add(alertId));
    setTimeout(() => {
      onDismiss?.(alertId);
    }, 300);
  };

  // Auto-hide alerts
  React.useEffect(() => {
    const timers: NodeJS.Timeout[] = [];

    alerts.forEach((alert) => {
      if (alert.autoHideDuration && !dismissedAlerts.has(alert.id)) {
        const timer = setTimeout(() => {
          handleDismiss(alert.id);
        }, alert.autoHideDuration);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach((timer) => clearTimeout(timer));
    };
  }, [alerts]);

  const visibleAlerts = alerts
    .filter((alert) => !dismissedAlerts.has(alert.id))
    .slice(0, maxAlerts);

  if (visibleAlerts.length === 0) {
    return null;
  }

  return (
    <div
      className={`space-y-3 ${
        position === 'top' ? 'mb-6' : 'mt-6'
      }`}
    >
      <AnimatePresence mode="popLayout">
        {visibleAlerts.map((alert) => {
          const config = alertConfig[alert.type];
          const Icon = config.icon;

          return (
            <motion.div
              key={alert.id}
              layout
              initial={{ opacity: 0, y: position === 'top' ? -20 : 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: 100 }}
              transition={{ duration: 0.2 }}
              className={`rounded-lg border ${config.borderColor} ${config.bgColor} p-4 shadow-sm`}
              role="alert"
              aria-live="polite"
            >
              <div className="flex items-start">
                {/* Icon */}
                <div className="flex-shrink-0">
                  <Icon
                    className={`h-5 w-5 ${config.iconColor}`}
                    aria-hidden="true"
                  />
                </div>

                {/* Content */}
                <div className="ml-3 flex-1">
                  <h3 className={`text-sm font-medium ${config.textColor}`}>
                    {alert.title}
                  </h3>
                  {alert.message && (
                    <div className={`mt-2 text-sm ${config.textColor}`}>
                      <p>{alert.message}</p>
                    </div>
                  )}
                  {alert.action && (
                    <div className="mt-3">
                      <button
                        type="button"
                        onClick={alert.action.onClick}
                        className={`inline-flex items-center rounded-md px-3 py-2 text-sm font-medium ${config.textColor} transition-colors hover:bg-white/50 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                          alert.type === 'success'
                            ? 'focus:ring-green-500'
                            : alert.type === 'error'
                            ? 'focus:ring-red-500'
                            : alert.type === 'warning'
                            ? 'focus:ring-yellow-500'
                            : 'focus:ring-blue-500'
                        }`}
                      >
                        {alert.action.label}
                        <ChevronRight className="ml-1 h-4 w-4" aria-hidden="true" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Dismiss button */}
                {alert.dismissible !== false && (
                  <div className="ml-auto flex-shrink-0 pl-3">
                    <button
                      type="button"
                      onClick={() => handleDismiss(alert.id)}
                      className={`inline-flex rounded-md ${config.bgColor} p-1.5 ${config.textColor} transition-colors hover:bg-white/50 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                        alert.type === 'success'
                          ? 'focus:ring-green-500'
                          : alert.type === 'error'
                          ? 'focus:ring-red-500'
                          : alert.type === 'warning'
                          ? 'focus:ring-yellow-500'
                          : 'focus:ring-blue-500'
                      }`}
                      aria-label="Dismiss alert"
                    >
                      <X className="h-5 w-5" aria-hidden="true" />
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
