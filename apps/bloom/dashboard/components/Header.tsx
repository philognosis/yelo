'use client';

import React, { Fragment, useState } from 'react';
import { Menu, Transition } from '@headlessui/react';
import {
  Bell,
  Search,
  Menu as MenuIcon,
  ChevronLeft,
  ChevronRight,
  User,
  Settings,
  HelpCircle,
  LogOut,
} from 'lucide-react';
import { motion } from 'framer-motion';
import WebSocketIndicator from './WebSocketIndicator';

export interface HeaderProps {
  userName: string;
  userAvatar?: string;
  userRole: 'employee' | 'manager' | 'admin';
  onMenuClick: () => void;
  onSidebarToggle: () => void;
  sidebarOpen: boolean;
  notificationCount?: number;
}

export default function Header({
  userName,
  userAvatar,
  userRole,
  onMenuClick,
  onSidebarToggle,
  sidebarOpen,
  notificationCount = 0,
}: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = () => {
    // Implement logout logic
    console.log('Logging out...');
  };

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Left section */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu button */}
          <button
            type="button"
            onClick={onMenuClick}
            className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 lg:hidden"
            aria-label="Open menu"
          >
            <MenuIcon className="h-6 w-6" aria-hidden="true" />
          </button>

          {/* Desktop sidebar toggle */}
          <button
            type="button"
            onClick={onSidebarToggle}
            className="hidden rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 lg:block"
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? (
              <ChevronLeft className="h-5 w-5" aria-hidden="true" />
            ) : (
              <ChevronRight className="h-5 w-5" aria-hidden="true" />
            )}
          </button>

          {/* Search bar */}
          <div className="hidden md:block">
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <Search className="h-5 w-5 text-gray-400" aria-hidden="true" />
              </div>
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search evaluations, people..."
                className="block w-64 rounded-md border-gray-300 pl-10 pr-3 py-2 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                aria-label="Search"
              />
            </div>
          </div>
        </div>

        {/* Right section */}
        <div className="flex items-center space-x-4">
          {/* WebSocket Status */}
          <WebSocketIndicator />

          {/* Notifications */}
          <button
            type="button"
            className="relative rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
            aria-label={`Notifications${notificationCount > 0 ? `, ${notificationCount} unread` : ''}`}
          >
            <Bell className="h-6 w-6" aria-hidden="true" />
            {notificationCount > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-medium text-white"
              >
                {notificationCount > 9 ? '9+' : notificationCount}
              </motion.span>
            )}
          </button>

          {/* User menu */}
          <Menu as="div" className="relative">
            <Menu.Button className="flex items-center space-x-3 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
              <span className="sr-only">Open user menu</span>
              <div className="flex items-center space-x-3">
                {userAvatar ? (
                  <img
                    src={userAvatar}
                    alt={userName}
                    className="h-8 w-8 rounded-full object-cover"
                  />
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600">
                    <span className="text-sm font-medium text-white">
                      {userName.charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium text-gray-700">{userName}</p>
                  <p className="text-xs capitalize text-gray-500">{userRole}</p>
                </div>
              </div>
            </Menu.Button>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                <div className="px-4 py-3">
                  <p className="text-sm font-medium text-gray-900">{userName}</p>
                  <p className="mt-0.5 text-xs capitalize text-gray-500">{userRole}</p>
                </div>
                <div className="py-1">
                  <Menu.Item>
                    {({ active }) => (
                      <a
                        href="/profile"
                        className={`${
                          active ? 'bg-gray-100' : ''
                        } flex items-center px-4 py-2 text-sm text-gray-700`}
                      >
                        <User className="mr-3 h-4 w-4" aria-hidden="true" />
                        Your Profile
                      </a>
                    )}
                  </Menu.Item>
                  <Menu.Item>
                    {({ active }) => (
                      <a
                        href="/settings"
                        className={`${
                          active ? 'bg-gray-100' : ''
                        } flex items-center px-4 py-2 text-sm text-gray-700`}
                      >
                        <Settings className="mr-3 h-4 w-4" aria-hidden="true" />
                        Settings
                      </a>
                    )}
                  </Menu.Item>
                  <Menu.Item>
                    {({ active }) => (
                      <a
                        href="/help"
                        className={`${
                          active ? 'bg-gray-100' : ''
                        } flex items-center px-4 py-2 text-sm text-gray-700`}
                      >
                        <HelpCircle className="mr-3 h-4 w-4" aria-hidden="true" />
                        Help & Support
                      </a>
                    )}
                  </Menu.Item>
                </div>
                <div className="py-1">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={handleLogout}
                        className={`${
                          active ? 'bg-gray-100' : ''
                        } flex w-full items-center px-4 py-2 text-sm text-red-700`}
                      >
                        <LogOut className="mr-3 h-4 w-4" aria-hidden="true" />
                        Sign out
                      </button>
                    )}
                  </Menu.Item>
                </div>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </header>
  );
}
