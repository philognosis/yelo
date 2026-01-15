'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Check, Sparkles, Users } from 'lucide-react';
import Button from './Button';
import Badge from './Badge';

export interface Peer {
  id: string;
  name: string;
  role: string;
  department: string;
  avatar?: string;
  workRelationship?: string;
  aiSuggested?: boolean;
  matchScore?: number;
}

export interface PeerSelectorProps {
  peers: Peer[];
  selectedPeers: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  maxPeers?: number;
  minPeers?: number;
  showAISuggestions?: boolean;
  isLoading?: boolean;
}

export default function PeerSelector({
  peers,
  selectedPeers,
  onSelectionChange,
  maxPeers = 5,
  minPeers = 3,
  showAISuggestions = true,
  isLoading = false,
}: PeerSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSuggestionsOnly, setShowSuggestionsOnly] = useState(false);

  const filteredPeers = peers.filter((peer) => {
    const matchesSearch =
      peer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      peer.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      peer.department.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSuggestionFilter = !showSuggestionsOnly || peer.aiSuggested;

    return matchesSearch && matchesSuggestionFilter;
  });

  const aiSuggestedPeers = peers
    .filter((p) => p.aiSuggested)
    .sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0));

  const handleTogglePeer = (peerId: string) => {
    if (selectedPeers.includes(peerId)) {
      onSelectionChange(selectedPeers.filter((id) => id !== peerId));
    } else if (selectedPeers.length < maxPeers) {
      onSelectionChange([...selectedPeers, peerId]);
    }
  };

  const handleSelectAllSuggested = () => {
    const suggestedIds = aiSuggestedPeers
      .slice(0, maxPeers)
      .map((p) => p.id);
    onSelectionChange(suggestedIds);
  };

  const isSelectionValid = selectedPeers.length >= minPeers && selectedPeers.length <= maxPeers;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Select Peer Reviewers</h3>
          <Badge variant={isSelectionValid ? 'green' : 'gray'}>
            {selectedPeers.length} / {maxPeers} selected
          </Badge>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          Select {minPeers}-{maxPeers} colleagues who can provide meaningful feedback
        </p>
      </div>

      {/* AI Suggestions Banner */}
      {showAISuggestions && aiSuggestedPeers.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-purple-200 bg-purple-50 p-4"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <Sparkles className="h-5 w-5 text-purple-600" aria-hidden="true" />
              <div>
                <h4 className="text-sm font-medium text-purple-900">
                  AI-Suggested Reviewers
                </h4>
                <p className="mt-1 text-sm text-purple-700">
                  Based on work relationships and collaboration history
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSelectAllSuggested}
              disabled={isLoading}
            >
              Select All
            </Button>
          </div>
        </motion.div>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
            aria-hidden="true"
          />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name, role, or department..."
            className="block w-full rounded-md border-gray-300 py-2 pl-10 pr-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            aria-label="Search peers"
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

        {showAISuggestions && (
          <Button
            variant={showSuggestionsOnly ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setShowSuggestionsOnly(!showSuggestionsOnly)}
            disabled={isLoading}
          >
            <Sparkles className="mr-2 h-4 w-4" aria-hidden="true" />
            AI Suggestions
          </Button>
        )}
      </div>

      {/* Peer List */}
      <div className="max-h-96 overflow-y-auto rounded-lg border border-gray-200">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 rounded-full bg-gray-200" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-1/3 rounded bg-gray-200" />
                    <div className="h-3 w-1/2 rounded bg-gray-200" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredPeers.length === 0 ? (
          <div className="py-12 text-center">
            <Users className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
            <p className="mt-2 text-sm text-gray-500">No peers found</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {filteredPeers.map((peer) => {
              const isSelected = selectedPeers.includes(peer.id);
              const canSelect = !isSelected && selectedPeers.length < maxPeers;

              return (
                <motion.button
                  key={peer.id}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={() => handleTogglePeer(peer.id)}
                  disabled={!isSelected && !canSelect}
                  className={`w-full border-b border-gray-200 p-4 text-left transition-colors last:border-b-0 ${
                    isSelected
                      ? 'bg-blue-50'
                      : canSelect
                      ? 'hover:bg-gray-50'
                      : 'cursor-not-allowed opacity-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {/* Avatar */}
                      <div className="relative">
                        {peer.avatar ? (
                          <img
                            src={peer.avatar}
                            alt={peer.name}
                            className="h-10 w-10 rounded-full object-cover"
                          />
                        ) : (
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600">
                            <span className="text-sm font-medium text-white">
                              {peer.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        )}
                        {peer.aiSuggested && (
                          <div
                            className="absolute -right-1 -top-1 rounded-full bg-purple-600 p-0.5"
                            aria-label="AI suggested"
                          >
                            <Sparkles className="h-3 w-3 text-white" aria-hidden="true" />
                          </div>
                        )}
                      </div>

                      {/* Info */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center space-x-2">
                          <p className="truncate text-sm font-medium text-gray-900">
                            {peer.name}
                          </p>
                          {peer.matchScore && (
                            <span className="text-xs text-purple-600">
                              {Math.round(peer.matchScore * 100)}% match
                            </span>
                          )}
                        </div>
                        <p className="truncate text-sm text-gray-500">
                          {peer.role} • {peer.department}
                        </p>
                        {peer.workRelationship && (
                          <p className="mt-0.5 text-xs text-gray-400">
                            {peer.workRelationship}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Selection indicator */}
                    <div
                      className={`flex h-5 w-5 items-center justify-center rounded border-2 ${
                        isSelected
                          ? 'border-blue-600 bg-blue-600'
                          : 'border-gray-300'
                      }`}
                    >
                      {isSelected && (
                        <Check className="h-4 w-4 text-white" aria-hidden="true" />
                      )}
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </AnimatePresence>
        )}
      </div>

      {/* Validation message */}
      {!isSelectionValid && selectedPeers.length > 0 && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-sm text-amber-600"
        >
          {selectedPeers.length < minPeers
            ? `Please select at least ${minPeers - selectedPeers.length} more peer${
                minPeers - selectedPeers.length !== 1 ? 's' : ''
              }`
            : `Please remove ${selectedPeers.length - maxPeers} peer${
                selectedPeers.length - maxPeers !== 1 ? 's' : ''
              }`}
        </motion.p>
      )}
    </div>
  );
}
