'use client';

import React, { Fragment } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { Check, ChevronDown } from 'lucide-react';
import { motion } from 'framer-motion';

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  value: string | number;
  onChange: (value: string | number) => void;
  options: SelectOption[];
  label?: string;
  placeholder?: string;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
}

export default function Select({
  value,
  onChange,
  options,
  label,
  placeholder = 'Select an option',
  error,
  helperText,
  disabled = false,
  required = false,
  id,
}: SelectProps) {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
  const selectedOption = options.find((opt) => opt.value === value);

  return (
    <div className="w-full">
      {/* Label */}
      {label && (
        <label
          htmlFor={selectId}
          className="mb-1 block text-sm font-medium text-gray-700"
        >
          {label}
          {required && <span className="ml-1 text-red-500">*</span>}
        </label>
      )}

      {/* Select */}
      <Listbox value={value} onChange={onChange} disabled={disabled}>
        {({ open }) => (
          <div className="relative">
            <Listbox.Button
              id={selectId}
              className={`relative w-full cursor-pointer rounded-md border ${
                error
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              } bg-white py-2 pl-3 pr-10 text-left text-sm shadow-sm transition-colors focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500`}
              aria-invalid={error ? 'true' : 'false'}
              aria-describedby={
                error
                  ? `${selectId}-error`
                  : helperText
                  ? `${selectId}-helper`
                  : undefined
              }
            >
              <span className={selectedOption ? 'block truncate' : 'block truncate text-gray-400'}>
                {selectedOption ? selectedOption.label : placeholder}
              </span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronDown
                  className={`h-5 w-5 text-gray-400 transition-transform ${
                    open ? 'rotate-180' : ''
                  }`}
                  aria-hidden="true"
                />
              </span>
            </Listbox.Button>

            <Transition
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-sm shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                {options.map((option) => (
                  <Listbox.Option
                    key={option.value}
                    value={option.value}
                    disabled={option.disabled}
                    className={({ active }) =>
                      `relative cursor-pointer select-none py-2 pl-10 pr-4 ${
                        active ? 'bg-blue-50 text-blue-900' : 'text-gray-900'
                      } ${option.disabled ? 'cursor-not-allowed opacity-50' : ''}`
                    }
                  >
                    {({ selected }) => (
                      <>
                        <span
                          className={`block truncate ${
                            selected ? 'font-semibold' : 'font-normal'
                          }`}
                        >
                          {option.label}
                        </span>
                        {selected && (
                          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-600">
                            <Check className="h-5 w-5" aria-hidden="true" />
                          </span>
                        )}
                      </>
                    )}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        )}
      </Listbox>

      {/* Error Message */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          id={`${selectId}-error`}
          className="mt-1 text-sm text-red-600"
          role="alert"
        >
          {error}
        </motion.p>
      )}

      {/* Helper Text */}
      {helperText && !error && (
        <p id={`${selectId}-helper`} className="mt-1 text-sm text-gray-500">
          {helperText}
        </p>
      )}
    </div>
  );
}
