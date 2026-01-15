'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Star, Info } from 'lucide-react';

export interface RatingOption {
  value: number;
  label: string;
  description?: string;
  color?: string;
}

export interface RatingSelectorProps {
  value?: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  options?: RatingOption[];
  label?: string;
  description?: string;
  showLabels?: boolean;
  showDescription?: boolean;
  disabled?: boolean;
  required?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const defaultOptions: RatingOption[] = [
  {
    value: 1,
    label: 'Needs Improvement',
    description: 'Performance below expectations',
    color: 'text-red-500',
  },
  {
    value: 2,
    label: 'Developing',
    description: 'Partially meets expectations',
    color: 'text-orange-500',
  },
  {
    value: 3,
    label: 'Meets Expectations',
    description: 'Consistently meets expectations',
    color: 'text-yellow-500',
  },
  {
    value: 4,
    label: 'Exceeds Expectations',
    description: 'Frequently exceeds expectations',
    color: 'text-lime-500',
  },
  {
    value: 5,
    label: 'Outstanding',
    description: 'Consistently exceeds expectations',
    color: 'text-green-500',
  },
];

const sizeConfig = {
  sm: {
    star: 'h-6 w-6',
    text: 'text-sm',
    spacing: 'space-x-1',
  },
  md: {
    star: 'h-8 w-8',
    text: 'text-base',
    spacing: 'space-x-2',
  },
  lg: {
    star: 'h-10 w-10',
    text: 'text-lg',
    spacing: 'space-x-3',
  },
};

export default function RatingSelector({
  value,
  onChange,
  min = 1,
  max = 5,
  step = 1,
  options = defaultOptions,
  label,
  description,
  showLabels = true,
  showDescription = true,
  disabled = false,
  required = false,
  size = 'md',
}: RatingSelectorProps) {
  const [hoveredValue, setHoveredValue] = useState<number | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);

  const config = sizeConfig[size];
  const displayValue = hoveredValue ?? value ?? 0;
  const selectedOption = options.find((opt) => opt.value === displayValue);

  const handleClick = (rating: number) => {
    if (!disabled) {
      onChange(rating);
    }
  };

  const renderStars = () => {
    const stars = [];
    for (let i = min; i <= max; i += step) {
      const isFilled = i <= displayValue;
      const isSelected = i === value;

      stars.push(
        <motion.button
          key={i}
          type="button"
          onClick={() => handleClick(i)}
          onMouseEnter={() => setHoveredValue(i)}
          onMouseLeave={() => setHoveredValue(null)}
          disabled={disabled}
          whileHover={{ scale: disabled ? 1 : 1.1 }}
          whileTap={{ scale: disabled ? 1 : 0.9 }}
          className={`transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded ${
            disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
          }`}
          aria-label={`Rate ${i} out of ${max}`}
        >
          <Star
            className={`${config.star} ${
              isFilled
                ? selectedOption?.color || 'text-yellow-500'
                : 'text-gray-300'
            } ${isFilled ? 'fill-current' : ''} ${
              isSelected && !hoveredValue ? 'drop-shadow-lg' : ''
            }`}
          />
        </motion.button>
      );
    }
    return stars;
  };

  return (
    <div className="space-y-3">
      {/* Label */}
      {label && (
        <div className="flex items-center space-x-2">
          <label className={`font-medium text-gray-900 ${config.text}`}>
            {label}
            {required && <span className="ml-1 text-red-500">*</span>}
          </label>
          {description && (
            <div className="group relative">
              <Info
                className="h-4 w-4 cursor-help text-gray-400"
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
              />
              {showTooltip && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="absolute left-0 top-full z-10 mt-2 w-64 rounded-md bg-gray-900 p-2 text-xs text-white shadow-lg"
                >
                  {description}
                </motion.div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Stars */}
      <div className={`flex items-center ${config.spacing}`}>
        {renderStars()}
        {value && (
          <motion.span
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="ml-3 text-sm font-medium text-gray-700"
          >
            {value}/{max}
          </motion.span>
        )}
      </div>

      {/* Selected Rating Info */}
      {showLabels && selectedOption && (
        <motion.div
          key={selectedOption.value}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-gray-200 bg-gray-50 p-3"
        >
          <div className="flex items-start space-x-2">
            <Star
              className={`h-5 w-5 flex-shrink-0 ${selectedOption.color} fill-current`}
              aria-hidden="true"
            />
            <div>
              <p className="text-sm font-medium text-gray-900">
                {selectedOption.label}
              </p>
              {showDescription && selectedOption.description && (
                <p className="mt-1 text-xs text-gray-600">
                  {selectedOption.description}
                </p>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Rating Scale Legend */}
      {showLabels && !value && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Rating Scale:</p>
          <div className="grid gap-2">
            {options.map((option) => (
              <div
                key={option.value}
                className="flex items-center space-x-2 text-sm"
              >
                <Star
                  className={`h-4 w-4 flex-shrink-0 ${option.color} fill-current`}
                  aria-hidden="true"
                />
                <span className="font-medium text-gray-700">{option.value}.</span>
                <span className="text-gray-600">{option.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
