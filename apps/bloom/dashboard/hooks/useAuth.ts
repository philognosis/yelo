/**
 * useAuth Hook
 * Hook for authentication state and actions
 */

import { useContext } from 'react';
import { AuthContext } from '@/contexts/AuthContext';

/**
 * Hook for accessing authentication context
 * Must be used within AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

export default useAuth;
