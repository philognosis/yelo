'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Info } from 'lucide-react';
import { useRouter } from 'next/navigation';

export interface PageHeaderProps {
  title: string;
  description?: string;
  showBackButton?: boolean;
  backHref?: string;
  actions?: React.ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  info?: string;
}

export default function PageHeader({
  title,
  description,
  showBackButton = false,
  backHref,
  actions,
  breadcrumbs,
  info,
}: PageHeaderProps) {
  const router = useRouter();

  const handleBack = () => {
    if (backHref) {
      router.push(backHref);
    } else {
      router.back();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-6"
    >
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="mb-4 flex" aria-label="Breadcrumb">
          <ol className="flex items-center space-x-2">
            {breadcrumbs.map((crumb, index) => (
              <li key={index} className="flex items-center">
                {index > 0 && (
                  <span className="mx-2 text-gray-400" aria-hidden="true">
                    /
                  </span>
                )}
                {crumb.href ? (
                  <a
                    href={crumb.href}
                    className="text-sm font-medium text-gray-500 hover:text-gray-700"
                  >
                    {crumb.label}
                  </a>
                ) : (
                  <span className="text-sm font-medium text-gray-900">
                    {crumb.label}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      <div className="sm:flex sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center">
            {showBackButton && (
              <button
                onClick={handleBack}
                className="mr-4 rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
                aria-label="Go back"
              >
                <ArrowLeft className="h-5 w-5" aria-hidden="true" />
              </button>
            )}
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
                  {title}
                </h1>
                {info && (
                  <div className="group relative">
                    <Info
                      className="h-5 w-5 text-gray-400 cursor-help"
                      aria-label="Additional information"
                    />
                    <div className="invisible absolute left-0 top-full z-10 mt-2 w-64 rounded-md bg-gray-900 p-3 text-xs text-white opacity-0 shadow-lg transition-all group-hover:visible group-hover:opacity-100">
                      {info}
                    </div>
                  </div>
                )}
              </div>
              {description && (
                <p className="mt-2 text-sm text-gray-500">{description}</p>
              )}
            </div>
          </div>
        </div>
        {actions && (
          <div className="mt-4 flex space-x-3 sm:ml-4 sm:mt-0">{actions}</div>
        )}
      </div>
    </motion.div>
  );
}
