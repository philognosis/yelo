'use client';

import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Mic, MicOff, Send, Loader2, Sparkles } from 'lucide-react';
import TextareaAutosize from 'react-textarea-autosize';
import Button from './Button';
import Badge from './Badge';

export interface FeedbackFormProps {
  onSubmit: (feedback: FeedbackData) => Promise<void>;
  placeholder?: string;
  minLength?: number;
  maxLength?: number;
  showVoiceInput?: boolean;
  showAIAssist?: boolean;
  categories?: string[];
  isLoading?: boolean;
}

export interface FeedbackData {
  text: string;
  category?: string;
  isVoiceInput: boolean;
}

export default function FeedbackForm({
  onSubmit,
  placeholder = 'Share your feedback...',
  minLength = 50,
  maxLength = 2000,
  showVoiceInput = true,
  showAIAssist = true,
  categories = [],
  isLoading = false,
}: FeedbackFormProps) {
  const [text, setText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState<string>('');
  const [showAiSuggestion, setShowAiSuggestion] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const charCount = text.length;
  const isValid = charCount >= minLength && charCount <= maxLength;
  const progress = Math.min((charCount / minLength) * 100, 100);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid || isLoading) return;

    try {
      await onSubmit({
        text,
        category: selectedCategory,
        isVoiceInput: isRecording,
      });
      setText('');
      setSelectedCategory(undefined);
      setAiSuggestion('');
      setShowAiSuggestion(false);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleVoiceToggle = async () => {
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
      }
    } else {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks: Blob[] = [];

        mediaRecorder.ondataavailable = (event) => {
          audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
          setIsProcessing(true);

          // Here you would send the audio to a speech-to-text service
          // For now, we'll simulate it
          setTimeout(() => {
            setText((prev) => prev + ' [Voice input transcribed]');
            setIsProcessing(false);
          }, 1500);

          stream.getTracks().forEach((track) => track.stop());
        };

        mediaRecorderRef.current = mediaRecorder;
        mediaRecorder.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Failed to start recording:', error);
      }
    }
  };

  const handleAIAssist = async () => {
    setIsProcessing(true);

    // Simulate AI suggestion
    setTimeout(() => {
      setAiSuggestion(
        'Consider structuring your feedback with specific examples and actionable suggestions. Here\'s a suggested improvement: ...'
      );
      setShowAiSuggestion(true);
      setIsProcessing(false);
    }, 1500);
  };

  const handleAcceptSuggestion = () => {
    setText(aiSuggestion);
    setShowAiSuggestion(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Category Selection */}
      {categories.length > 0 && (
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            Category
          </label>
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => setSelectedCategory(category)}
                className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Text Input */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <label htmlFor="feedback-text" className="text-sm font-medium text-gray-700">
            Your Feedback
          </label>
          <div className="flex items-center space-x-2">
            {isRecording && (
              <Badge variant="red">
                <span className="animate-pulse">Recording...</span>
              </Badge>
            )}
            {isProcessing && (
              <Badge variant="blue">
                <Loader2 className="mr-1 h-3 w-3 animate-spin" aria-hidden="true" />
                Processing...
              </Badge>
            )}
          </div>
        </div>

        <div className="relative">
          <TextareaAutosize
            id="feedback-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={placeholder}
            minRows={4}
            maxRows={12}
            maxLength={maxLength}
            disabled={isRecording || isProcessing || isLoading}
            className="block w-full rounded-lg border-gray-300 pr-12 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-50"
            aria-label="Feedback text"
            aria-describedby="char-count"
          />

          {/* Voice Input Button */}
          {showVoiceInput && (
            <button
              type="button"
              onClick={handleVoiceToggle}
              disabled={isProcessing || isLoading}
              className={`absolute bottom-3 right-3 rounded-full p-2 transition-colors ${
                isRecording
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              } disabled:cursor-not-allowed disabled:opacity-50`}
              aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
            >
              {isRecording ? (
                <MicOff className="h-5 w-5" aria-hidden="true" />
              ) : (
                <Mic className="h-5 w-5" aria-hidden="true" />
              )}
            </button>
          )}
        </div>

        {/* Character Count and Progress */}
        <div className="mt-2">
          <div className="flex items-center justify-between text-xs">
            <span
              id="char-count"
              className={`${
                charCount < minLength
                  ? 'text-gray-500'
                  : charCount > maxLength
                  ? 'text-red-600'
                  : 'text-green-600'
              }`}
            >
              {charCount} / {maxLength} characters
              {charCount < minLength && ` (${minLength - charCount} more needed)`}
            </span>
            <span className="text-gray-500">{Math.round(progress)}% complete</span>
          </div>
          <div className="mt-1 h-1 overflow-hidden rounded-full bg-gray-200">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(progress, 100)}%` }}
              className={`h-full transition-colors ${
                progress >= 100 ? 'bg-green-500' : 'bg-blue-500'
              }`}
            />
          </div>
        </div>
      </div>

      {/* AI Suggestion */}
      {showAiSuggestion && aiSuggestion && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-purple-200 bg-purple-50 p-4"
        >
          <div className="mb-2 flex items-center space-x-2">
            <Sparkles className="h-4 w-4 text-purple-600" aria-hidden="true" />
            <h4 className="text-sm font-medium text-purple-900">AI Suggestion</h4>
          </div>
          <p className="text-sm text-purple-700">{aiSuggestion}</p>
          <div className="mt-3 flex space-x-2">
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={handleAcceptSuggestion}
            >
              Use This
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowAiSuggestion(false)}
            >
              Dismiss
            </Button>
          </div>
        </motion.div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div>
          {showAIAssist && !showAiSuggestion && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleAIAssist}
              disabled={isProcessing || isLoading || charCount < 10}
            >
              <Sparkles className="mr-2 h-4 w-4" aria-hidden="true" />
              Get AI Help
            </Button>
          )}
        </div>

        <Button
          type="submit"
          variant="primary"
          disabled={!isValid || isLoading || isProcessing}
          isLoading={isLoading}
        >
          <Send className="mr-2 h-4 w-4" aria-hidden="true" />
          Submit Feedback
        </Button>
      </div>
    </form>
  );
}
