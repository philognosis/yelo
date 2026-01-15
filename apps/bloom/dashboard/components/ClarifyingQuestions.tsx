'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Send, Sparkles, User, Bot, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Button from './Button';

export interface Question {
  id: string;
  question: string;
  context?: string;
  timestamp: Date | string;
}

export interface Answer {
  id: string;
  questionId: string;
  answer: string;
  timestamp: Date | string;
}

export interface Conversation {
  id: string;
  question: Question;
  answer?: Answer;
  aiResponse?: string;
  aiResponseTimestamp?: Date | string;
}

export interface ClarifyingQuestionsProps {
  conversations: Conversation[];
  onAnswerSubmit: (questionId: string, answer: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
}

export default function ClarifyingQuestions({
  conversations,
  onAnswerSubmit,
  isLoading = false,
  placeholder = 'Type your answer...',
}: ClarifyingQuestionsProps) {
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (questionId: string) => {
    if (!answerText.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onAnswerSubmit(questionId, answerText);
      setAnswerText('');
      setActiveQuestionId(null);
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (timestamp: Date | string) => {
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return formatDistanceToNow(date, { addSuffix: true });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-2">
        <MessageSquare className="h-5 w-5 text-blue-600" aria-hidden="true" />
        <h3 className="text-lg font-semibold text-gray-900">
          Clarifying Questions
        </h3>
        {conversations.filter((c) => !c.answer).length > 0 && (
          <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
            {conversations.filter((c) => !c.answer).length} pending
          </span>
        )}
      </div>

      {isLoading && conversations.length === 0 ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-4">
              <div className="mb-3 space-y-2">
                <div className="h-4 w-3/4 rounded bg-gray-200" />
                <div className="h-3 w-1/2 rounded bg-gray-200" />
              </div>
            </div>
          ))}
        </div>
      ) : conversations.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 p-12 text-center">
          <MessageSquare className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No questions yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            The AI will ask clarifying questions as needed
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {conversations.map((conversation, index) => {
              const isActive = activeQuestionId === conversation.question.id;
              const hasAnswer = !!conversation.answer;

              return (
                <motion.div
                  key={conversation.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  className={`rounded-lg border ${
                    hasAnswer ? 'border-green-200 bg-green-50' : 'border-blue-200 bg-blue-50'
                  } p-4`}
                >
                  {/* AI Question */}
                  <div className="mb-3 flex items-start space-x-3">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-blue-600">
                      <Bot className="h-5 w-5 text-white" aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">AI Assistant</span>
                        <span className="text-xs text-gray-500">
                          {formatTime(conversation.question.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-800">{conversation.question.question}</p>
                      {conversation.question.context && (
                        <p className="mt-1 text-xs text-gray-600">
                          Context: {conversation.question.context}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* User Answer */}
                  {hasAnswer ? (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="ml-11 rounded-lg border border-gray-200 bg-white p-3"
                    >
                      <div className="mb-1 flex items-center space-x-2">
                        <User className="h-4 w-4 text-gray-600" aria-hidden="true" />
                        <span className="text-sm font-medium text-gray-900">You</span>
                        <span className="text-xs text-gray-500">
                          {formatTime(conversation.answer.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-800">{conversation.answer.answer}</p>
                    </motion.div>
                  ) : isActive ? (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="ml-11 space-y-3"
                    >
                      <textarea
                        value={answerText}
                        onChange={(e) => setAnswerText(e.target.value)}
                        placeholder={placeholder}
                        rows={3}
                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        autoFocus
                      />
                      <div className="flex justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setActiveQuestionId(null);
                            setAnswerText('');
                          }}
                          disabled={isSubmitting}
                        >
                          Cancel
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleSubmit(conversation.question.id)}
                          disabled={!answerText.trim() || isSubmitting}
                          isLoading={isSubmitting}
                        >
                          <Send className="mr-2 h-4 w-4" aria-hidden="true" />
                          Submit
                        </Button>
                      </div>
                    </motion.div>
                  ) : (
                    <div className="ml-11">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setActiveQuestionId(conversation.question.id)}
                      >
                        Answer Question
                      </Button>
                    </div>
                  )}

                  {/* AI Response to Answer */}
                  {conversation.aiResponse && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="ml-11 mt-3 rounded-lg border border-purple-200 bg-purple-50 p-3"
                    >
                      <div className="mb-1 flex items-center space-x-2">
                        <Sparkles className="h-4 w-4 text-purple-600" aria-hidden="true" />
                        <span className="text-sm font-medium text-purple-900">AI Response</span>
                        {conversation.aiResponseTimestamp && (
                          <span className="text-xs text-purple-600">
                            {formatTime(conversation.aiResponseTimestamp)}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-purple-800">{conversation.aiResponse}</p>
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
