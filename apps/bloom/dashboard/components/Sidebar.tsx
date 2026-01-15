'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Users,
  FileText,
  BarChart3,
  Settings,
  Bell,
  Calendar,
  MessageSquare,
  Award,
  Activity,
} from 'lucide-react';

export interface SidebarProps {
  userRole: 'employee' | 'manager' | 'admin';
  isOpen: boolean;
  mobileMenuOpen: boolean;
  onMobileMenuClose: () => void;
}

interface MenuItem {
  name: string;
  href: string;
  icon: React.ElementType;
  roles: ('employee' | 'manager' | 'admin')[];
  badge?: number;
}

const menuItems: MenuItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: Home, roles: ['employee', 'manager', 'admin'] },
  { name: 'My Evaluations', href: '/evaluations', icon: FileText, roles: ['employee', 'manager', 'admin'] },
  { name: 'Team Evaluations', href: '/team', icon: Users, roles: ['manager', 'admin'] },
  { name: 'Peer Selection', href: '/peers', icon: Award, roles: ['employee', 'manager', 'admin'] },
  { name: 'Feedback', href: '/feedback', icon: MessageSquare, roles: ['employee', 'manager', 'admin'] },
  { name: 'Analytics', href: '/analytics', icon: BarChart3, roles: ['manager', 'admin'] },
  { name: 'Calendar', href: '/calendar', icon: Calendar, roles: ['employee', 'manager', 'admin'] },
  { name: 'Activity', href: '/activity', icon: Activity, roles: ['manager', 'admin'] },
  { name: 'Notifications', href: '/notifications', icon: Bell, roles: ['employee', 'manager', 'admin'] },
  { name: 'Settings', href: '/settings', icon: Settings, roles: ['employee', 'manager', 'admin'] },
];

export default function Sidebar({
  userRole,
  isOpen,
  mobileMenuOpen,
  onMobileMenuClose,
}: SidebarProps) {
  const pathname = usePathname();

  const filteredMenuItems = menuItems.filter((item) =>
    item.roles.includes(userRole)
  );

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-gray-200 bg-white px-4">
        <motion.div
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          className="flex items-center space-x-2"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-purple-600">
            <span className="text-xl font-bold text-white">B</span>
          </div>
          {isOpen && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="text-xl font-bold text-gray-900"
            >
              Bloom
            </motion.span>
          )}
        </motion.div>
      </div>

      {/* Navigation */}
      <nav
        className="flex-1 space-y-1 overflow-y-auto bg-white px-3 py-4"
        aria-label="Main navigation"
      >
        {filteredMenuItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={onMobileMenuClose}
              className={`group relative flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              }`}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon
                className={`h-5 w-5 flex-shrink-0 ${
                  isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'
                }`}
                aria-hidden="true"
              />
              {isOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="ml-3"
                >
                  {item.name}
                </motion.span>
              )}
              {item.badge && isOpen && (
                <span className="ml-auto inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-600">
                  {item.badge}
                </span>
              )}
              {!isOpen && (
                <div className="absolute left-full top-1/2 z-50 ml-2 hidden -translate-y-1/2 rounded-md bg-gray-900 px-2 py-1 text-xs text-white group-hover:block">
                  {item.name}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Role badge */}
      {isOpen && (
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500">Role</span>
            <span className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium capitalize text-purple-800">
              {userRole}
            </span>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isOpen ? 256 : 80 }}
        transition={{ duration: 0.3 }}
        className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:flex-col"
      >
        <SidebarContent />
      </motion.aside>

      {/* Mobile sidebar */}
      {mobileMenuOpen && (
        <motion.aside
          initial={{ x: -256 }}
          animate={{ x: 0 }}
          exit={{ x: -256 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-y-0 z-50 flex w-64 flex-col lg:hidden"
        >
          <SidebarContent />
        </motion.aside>
      )}
    </>
  );
}
