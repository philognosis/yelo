'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import Header from './Header';

export interface DashboardLayoutProps {
  children: React.ReactNode;
  userRole: 'employee' | 'manager' | 'admin';
  userName: string;
  userAvatar?: string;
}

export default function DashboardLayout({
  children,
  userRole,
  userName,
  userAvatar,
}: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu backdrop */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-gray-900/50 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <Sidebar
        userRole={userRole}
        isOpen={sidebarOpen}
        mobileMenuOpen={mobileMenuOpen}
        onMobileMenuClose={() => setMobileMenuOpen(false)}
      />

      {/* Main content */}
      <div
        className={`transition-all duration-300 ${
          sidebarOpen ? 'lg:pl-64' : 'lg:pl-20'
        }`}
      >
        {/* Header */}
        <Header
          userName={userName}
          userAvatar={userAvatar}
          userRole={userRole}
          onMenuClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          sidebarOpen={sidebarOpen}
        />

        {/* Page content */}
        <motion.main
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="px-4 py-6 sm:px-6 lg:px-8"
        >
          {children}
        </motion.main>
      </div>
    </div>
  );
}
