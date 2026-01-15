'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';

export interface WebSocketIndicatorProps {
  status?: 'connected' | 'disconnected' | 'connecting' | 'error';
  onReconnect?: () => void;
  showLabel?: boolean;
  showTooltip?: boolean;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export default function WebSocketIndicator({
  status = 'connected',
  onReconnect,
  showLabel = false,
  showTooltip = true,
  autoReconnect = true,
  reconnectInterval = 5000,
}: WebSocketIndicatorProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  useEffect(() => {
    if (!autoReconnect || status !== 'disconnected') return;

    const timer = setTimeout(() => {
      setReconnectAttempt((prev) => prev + 1);
      onReconnect?.();
    }, reconnectInterval);

    return () => clearTimeout(timer);
  }, [autoReconnect, status, reconnectInterval, reconnectAttempt, onReconnect]);

  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          label: 'Connected',
          pulse: false,
        };
      case 'connecting':
        return {
          icon: Wifi,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          label: 'Connecting...',
          pulse: true,
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          label: 'Disconnected',
          pulse: false,
        };
      case 'error':
        return {
          icon: AlertCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          label: 'Connection Error',
          pulse: false,
        };
      default:
        return {
          icon: Wifi,
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          label: 'Unknown',
          pulse: false,
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const handleClick = () => {
    if ((status === 'disconnected' || status === 'error') && onReconnect) {
      onReconnect();
    }
  };

  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <motion.button
        type="button"
        onClick={handleClick}
        whileHover={
          status === 'disconnected' || status === 'error' ? { scale: 1.05 } : {}
        }
        whileTap={
          status === 'disconnected' || status === 'error' ? { scale: 0.95 } : {}
        }
        className={`relative inline-flex items-center space-x-2 rounded-full p-2 transition-colors ${
          status === 'disconnected' || status === 'error'
            ? 'cursor-pointer hover:bg-gray-100'
            : 'cursor-default'
        }`}
        aria-label={`Connection status: ${config.label}`}
      >
        {/* Pulse animation for connecting/error states */}
        {config.pulse && (
          <motion.span
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.5, 0, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className={`absolute inset-0 rounded-full ${config.bgColor}`}
            aria-hidden="true"
          />
        )}

        {/* Icon */}
        <div className="relative">
          <Icon className={`h-5 w-5 ${config.color}`} aria-hidden="true" />
          {status === 'connected' && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-green-500"
              aria-hidden="true"
            />
          )}
        </div>

        {/* Label (optional) */}
        {showLabel && (
          <span className={`text-sm font-medium ${config.color}`}>
            {config.label}
          </span>
        )}
      </motion.button>

      {/* Tooltip */}
      {showTooltip && isHovered && (
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full z-50 mt-2 w-48 rounded-md bg-gray-900 p-3 text-xs text-white shadow-lg"
            role="tooltip"
          >
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-medium">Status:</span>
                <span className={config.color.replace('text-', 'text-white')}>
                  {config.label}
                </span>
              </div>
              {status === 'disconnected' && autoReconnect && (
                <div className="text-gray-300">
                  Auto-reconnecting in {Math.ceil(reconnectInterval / 1000)}s
                </div>
              )}
              {(status === 'disconnected' || status === 'error') && onReconnect && (
                <div className="mt-2 text-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onReconnect();
                    }}
                    className="rounded bg-white/20 px-2 py-1 text-xs font-medium hover:bg-white/30"
                  >
                    Reconnect Now
                  </button>
                </div>
              )}
            </div>
            {/* Arrow */}
            <div
              className="absolute -top-1 right-4 h-2 w-2 rotate-45 bg-gray-900"
              aria-hidden="true"
            />
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
