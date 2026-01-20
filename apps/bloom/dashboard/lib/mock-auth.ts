/**
 * Mock Authentication System
 * Provides demo authentication without requiring a backend API
 */

import { User, AuthResponse } from '@/types/user';

/**
 * Demo user accounts with different roles
 */
const DEMO_USERS: Record<string, { email: string; password: string; user: User }> = {
  'employee@example.com': {
    email: 'employee@example.com',
    password: 'demo-password',
    user: {
      id: 'emp-001',
      email: 'employee@example.com',
      username: 'employee',
      full_name: 'John Employee',
      role: 'employee' as any,
      department: 'Engineering',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  },
  'manager@example.com': {
    email: 'manager@example.com',
    password: 'demo-password',
    user: {
      id: 'mgr-001',
      email: 'manager@example.com',
      username: 'manager',
      full_name: 'Jane Manager',
      role: 'evaluator' as any,
      department: 'Engineering',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  },
  'hr@example.com': {
    email: 'hr@example.com',
    password: 'demo-password',
    user: {
      id: 'hr-001',
      email: 'hr@example.com',
      username: 'hradmin',
      full_name: 'HR Administrator',
      role: 'admin' as any,
      department: 'Human Resources',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  },
  'committee@example.com': {
    email: 'committee@example.com',
    password: 'demo-password',
    user: {
      id: 'com-001',
      email: 'committee@example.com',
      username: 'committee',
      full_name: 'Committee Member',
      role: 'admin' as any,
      department: 'Human Resources',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  },
};

/**
 * Mock login function
 * Simulates API authentication with demo accounts
 */
export async function mockLogin(email: string, password: string): Promise<AuthResponse> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500));

  const demoUser = DEMO_USERS[email.toLowerCase()];

  if (!demoUser || demoUser.password !== password) {
    throw new Error('Invalid email or password');
  }

  // Generate a mock JWT token
  const token = btoa(JSON.stringify({
    email: demoUser.email,
    id: demoUser.user.id,
    exp: Date.now() + 24 * 60 * 60 * 1000 // 24 hours
  }));

  return {
    token: {
      access_token: token,
      token_type: 'Bearer',
      expires_in: 86400, // 24 hours
      issued_at: Date.now(),
    },
    user: demoUser.user,
  };
}

/**
 * Mock logout function
 */
export async function mockLogout(): Promise<void> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 300));
  return;
}

/**
 * Mock get current user function
 */
export async function mockGetCurrentUser(token: string): Promise<User> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 300));

  try {
    const decoded = JSON.parse(atob(token));
    const demoUser = Object.values(DEMO_USERS).find(
      (u) => u.user.id === decoded.id
    );

    if (!demoUser) {
      throw new Error('User not found');
    }

    return demoUser.user;
  } catch (error) {
    throw new Error('Invalid token');
  }
}

/**
 * Check if we should use mock auth
 * Returns true if no backend API is configured or available
 */
export function shouldUseMockAuth(): boolean {
  // Always use mock auth in development when no backend is running
  // This is the safest default for demo purposes

  // Check if explicitly disabled via environment variable
  if (typeof window !== 'undefined') {
    // Client-side check
    const useMock = localStorage.getItem('USE_MOCK_AUTH');
    if (useMock === 'false') {
      return false;
    }
  }

  // Default to mock auth (safest for demo mode)
  return true;

  // To enable real API, set localStorage.setItem('USE_MOCK_AUTH', 'false') in browser console
  // or set NEXT_PUBLIC_USE_REAL_API=true environment variable
}
