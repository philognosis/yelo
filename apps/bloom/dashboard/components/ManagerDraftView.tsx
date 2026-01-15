'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Edit3, Check, X, Sparkles, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Button from './Button';
import Badge from './Badge';
import EvidenceMap from './EvidenceMap';

export interface Evidence {
  id: string;
  type: 'peer_feedback' | 'self_review' | 'metric' | 'project' | 'incident';
  source: string;
  content: string;
  timestamp: Date | string;
  relevance?: number;
  linkedClaims?: string[];
}

export interface DraftSection {
  id: string;
  title: string;
  content: string;
  rating?: number;
  evidence: Evidence[];
  isEditing?: boolean;
}

export interface ManagerDraftViewProps {
  employeeName: string;
  period: string;
  sections: DraftSection[];
  overallRating?: number;
  confidence?: number;
  onEdit: (sectionId: string, newContent: string) => void;
  onApprove: () => void;
  onRequestRevision: () => void;
  isLoading?: boolean;
  showEvidence?: boolean;
}

export default function ManagerDraftView({
  employeeName,
  period,
  sections,
  overallRating,
  confidence = 0,
  onEdit,
  onApprove,
  onRequestRevision,
  isLoading = false,
  showEvidence = true,
}: ManagerDraftViewProps) {
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [showEvidenceMap, setShowEvidenceMap] = useState(false);

  const handleStartEdit = (section: DraftSection) => {
    setEditingSectionId(section.id);
    setEditContent(section.content);
  };

  const handleSaveEdit = () => {
    if (editingSectionId) {
      onEdit(editingSectionId, editContent);
      setEditingSectionId(null);
      setEditContent('');
    }
  };

  const handleCancelEdit = () => {
    setEditingSectionId(null);
    setEditContent('');
  };

  const allEvidence = sections.flatMap((section) => section.evidence);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-purple-200 bg-gradient-to-r from-purple-50 to-blue-50 p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <Sparkles className="h-6 w-6 text-purple-600" aria-hidden="true" />
              <h2 className="text-2xl font-bold text-gray-900">
                AI-Generated Evaluation Draft
              </h2>
            </div>
            <p className="mt-2 text-gray-700">
              {employeeName} • {period}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              {overallRating && (
                <Badge variant="blue">
                  Overall Rating: {overallRating}/5
                </Badge>
              )}
              <Badge variant={confidence > 0.8 ? 'green' : confidence > 0.6 ? 'yellow' : 'red'}>
                Confidence: {Math.round(confidence * 100)}%
              </Badge>
              <Badge variant="purple">
                {allEvidence.length} Evidence Points
              </Badge>
            </div>
          </div>
          {showEvidence && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowEvidenceMap(!showEvidenceMap)}
            >
              <ExternalLink className="mr-2 h-4 w-4" aria-hidden="true" />
              {showEvidenceMap ? 'Hide' : 'Show'} Evidence Map
            </Button>
          )}
        </div>
      </div>

      {/* Evidence Map */}
      {showEvidenceMap && showEvidence && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          <EvidenceMap evidence={allEvidence} />
        </motion.div>
      )}

      {/* Sections */}
      <div className="space-y-6">
        {sections.map((section, index) => {
          const isEditing = editingSectionId === section.id;

          return (
            <motion.div
              key={section.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
            >
              {/* Section Header */}
              <div className="mb-4 flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {section.title}
                    </h3>
                    {section.rating && (
                      <Badge variant="blue">
                        {section.rating}/5
                      </Badge>
                    )}
                  </div>
                  {showEvidence && section.evidence.length > 0 && (
                    <p className="mt-1 text-sm text-gray-500">
                      Based on {section.evidence.length} evidence point{section.evidence.length !== 1 ? 's' : ''}
                    </p>
                  )}
                </div>
                {!isEditing && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleStartEdit(section)}
                    disabled={isLoading}
                  >
                    <Edit3 className="mr-2 h-4 w-4" aria-hidden="true" />
                    Edit
                  </Button>
                )}
              </div>

              {/* Content */}
              {isEditing ? (
                <div className="space-y-3">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={8}
                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    placeholder="Edit section content..."
                  />
                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCancelEdit}
                    >
                      <X className="mr-2 h-4 w-4" aria-hidden="true" />
                      Cancel
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleSaveEdit}
                    >
                      <Check className="mr-2 h-4 w-4" aria-hidden="true" />
                      Save
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{section.content}</ReactMarkdown>
                </div>
              )}

              {/* Evidence Preview */}
              {showEvidence && section.evidence.length > 0 && !isEditing && (
                <div className="mt-4 border-t border-gray-200 pt-4">
                  <h4 className="mb-2 flex items-center text-sm font-medium text-gray-700">
                    <FileText className="mr-2 h-4 w-4" aria-hidden="true" />
                    Supporting Evidence
                  </h4>
                  <div className="space-y-2">
                    {section.evidence.slice(0, 3).map((evidence) => (
                      <div
                        key={evidence.id}
                        className="rounded-md border border-gray-200 bg-gray-50 p-3"
                      >
                        <div className="mb-1 flex items-center justify-between">
                          <span className="text-xs font-medium capitalize text-gray-600">
                            {evidence.type.replace('_', ' ')}
                          </span>
                          <span className="text-xs text-gray-500">{evidence.source}</span>
                        </div>
                        <p className="text-sm text-gray-700 line-clamp-2">
                          {evidence.content}
                        </p>
                      </div>
                    ))}
                    {section.evidence.length > 3 && (
                      <button
                        onClick={() => setShowEvidenceMap(true)}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        +{section.evidence.length - 3} more evidence points
                      </button>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-6">
        <div>
          <p className="text-sm text-gray-600">
            Review the AI-generated draft and make any necessary edits before approval
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="secondary"
            onClick={onRequestRevision}
            disabled={isLoading}
          >
            Request Revision
          </Button>
          <Button
            variant="primary"
            onClick={onApprove}
            disabled={isLoading}
            isLoading={isLoading}
          >
            <Check className="mr-2 h-4 w-4" aria-hidden="true" />
            Approve Draft
          </Button>
        </div>
      </div>
    </div>
  );
}
