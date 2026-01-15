'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  MessageSquare,
  BarChart3,
  Briefcase,
  AlertCircle,
  Search,
  Filter,
  X,
} from 'lucide-react';
import { format } from 'date-fns';
import Badge from './Badge';

export interface Evidence {
  id: string;
  type: 'peer_feedback' | 'self_review' | 'metric' | 'project' | 'incident';
  source: string;
  content: string;
  timestamp: Date | string;
  relevance?: number;
  linkedClaims?: string[];
}

export interface EvidenceMapProps {
  evidence: Evidence[];
  onEvidenceSelect?: (evidenceId: string) => void;
  showFilters?: boolean;
}

const evidenceTypeConfig = {
  peer_feedback: {
    icon: MessageSquare,
    label: 'Peer Feedback',
    color: 'bg-purple-100 text-purple-700 border-purple-300',
  },
  self_review: {
    icon: FileText,
    label: 'Self Review',
    color: 'bg-blue-100 text-blue-700 border-blue-300',
  },
  metric: {
    icon: BarChart3,
    label: 'Metric',
    color: 'bg-green-100 text-green-700 border-green-300',
  },
  project: {
    icon: Briefcase,
    label: 'Project',
    color: 'bg-indigo-100 text-indigo-700 border-indigo-300',
  },
  incident: {
    icon: AlertCircle,
    label: 'Incident',
    color: 'bg-red-100 text-red-700 border-red-300',
  },
};

export default function EvidenceMap({
  evidence,
  onEvidenceSelect,
  showFilters = true,
}: EvidenceMapProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<Set<Evidence['type']>>(new Set());
  const [sortBy, setSortBy] = useState<'relevance' | 'date'>('relevance');

  const handleTypeToggle = (type: Evidence['type']) => {
    const newSelected = new Set(selectedTypes);
    if (newSelected.has(type)) {
      newSelected.delete(type);
    } else {
      newSelected.add(type);
    }
    setSelectedTypes(newSelected);
  };

  const filteredEvidence = evidence
    .filter((item) => {
      // Type filter
      if (selectedTypes.size > 0 && !selectedTypes.has(item.type)) {
        return false;
      }

      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          item.content.toLowerCase().includes(query) ||
          item.source.toLowerCase().includes(query)
        );
      }

      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'relevance') {
        return (b.relevance || 0) - (a.relevance || 0);
      } else {
        const dateA = typeof a.timestamp === 'string' ? new Date(a.timestamp) : a.timestamp;
        const dateB = typeof b.timestamp === 'string' ? new Date(b.timestamp) : b.timestamp;
        return dateB.getTime() - dateA.getTime();
      }
    });

  const evidenceByType = Object.keys(evidenceTypeConfig).reduce((acc, type) => {
    acc[type as Evidence['type']] = evidence.filter((e) => e.type === type).length;
    return acc;
  }, {} as Record<Evidence['type'], number>);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Evidence Map</h3>
        <p className="mt-1 text-sm text-gray-500">
          {filteredEvidence.length} of {evidence.length} evidence points
        </p>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="mb-6 space-y-4">
          {/* Search */}
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
              aria-hidden="true"
            />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search evidence..."
              className="block w-full rounded-md border-gray-300 py-2 pl-10 pr-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            )}
          </div>

          {/* Type Filters */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Filter by Type</span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setSortBy('relevance')}
                  className={`text-xs ${
                    sortBy === 'relevance'
                      ? 'font-medium text-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Relevance
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={() => setSortBy('date')}
                  className={`text-xs ${
                    sortBy === 'date'
                      ? 'font-medium text-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Date
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(evidenceTypeConfig).map(([type, config]) => {
                const count = evidenceByType[type as Evidence['type']];
                const isSelected = selectedTypes.has(type as Evidence['type']);
                const Icon = config.icon;

                return (
                  <button
                    key={type}
                    onClick={() => handleTypeToggle(type as Evidence['type'])}
                    className={`inline-flex items-center space-x-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
                      isSelected
                        ? config.color
                        : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    <span>{config.label}</span>
                    <span className="rounded-full bg-white/50 px-1.5 text-xs">
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Evidence List */}
      <div className="space-y-3">
        {filteredEvidence.length === 0 ? (
          <div className="py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
            <p className="mt-2 text-sm text-gray-500">No evidence found</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {filteredEvidence.map((item, index) => {
              const config = evidenceTypeConfig[item.type];
              const Icon = config.icon;
              const date = typeof item.timestamp === 'string' ? new Date(item.timestamp) : item.timestamp;

              return (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.03 }}
                  onClick={() => onEvidenceSelect?.(item.id)}
                  className={`cursor-pointer rounded-lg border p-4 transition-all hover:shadow-md ${
                    onEvidenceSelect ? 'hover:border-blue-300' : ''
                  }`}
                >
                  {/* Header */}
                  <div className="mb-2 flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <div className={`rounded-lg border p-1.5 ${config.color}`}>
                        <Icon className="h-4 w-4" aria-hidden="true" />
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-900">
                          {config.label}
                        </span>
                        <span className="mx-1.5 text-gray-300">•</span>
                        <span className="text-sm text-gray-600">{item.source}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {item.relevance !== undefined && (
                        <Badge
                          variant={
                            item.relevance > 0.8
                              ? 'green'
                              : item.relevance > 0.5
                              ? 'yellow'
                              : 'gray'
                          }
                        >
                          {Math.round(item.relevance * 100)}% relevant
                        </Badge>
                      )}
                      <span className="text-xs text-gray-500">
                        {format(date, 'MMM d, yyyy')}
                      </span>
                    </div>
                  </div>

                  {/* Content */}
                  <p className="text-sm text-gray-700">{item.content}</p>

                  {/* Linked Claims */}
                  {item.linkedClaims && item.linkedClaims.length > 0 && (
                    <div className="mt-3 flex items-start space-x-2">
                      <span className="text-xs font-medium text-gray-500">Supports:</span>
                      <div className="flex flex-wrap gap-1">
                        {item.linkedClaims.map((claim, i) => (
                          <Badge key={i} variant="blue">
                            {claim}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
