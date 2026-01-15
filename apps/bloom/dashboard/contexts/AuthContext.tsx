/**
 * Authentication Context
 * Provides authentication state and actions throughout the app
 */

'use client';

import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { User, LoginCredentials, AuthResponse } from '@/types/user';
import { apiClient } from '@/lib/api-client';
import {
  getStoredUser,
  storeAuth,
  clearAuth,
  isAuthenticated as checkIsAuthenticated,
  getAuthToken,
  isTokenExpiringSoon,
  getRefreshToken,
} from '@/lib/auth';

/**
 * Authentication Context State
 */
interface AuthContextState {
  // Current user
  user: User | null;

  // Authentication state
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;

  // Error state
  error: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

/**
 * Create context with undefined default
 */
export const AuthContext = createContext<AuthContextState | undefined>(undefined);

/**
 * Provider Props
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 * Manages authentication state and provides auth actions
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Initialize authentication state from storage
   */
  const initialize = useCallback(async () => {
    try {
      // Check if user is authenticated
      if (checkIsAuthenticated()) {
        const storedUser = getStoredUser();
        if (storedUser) {
          setUser(storedUser);

          // Fetch fresh user data in background
          try {
            const response = await apiClient.getCurrentUser();
            if (response.success && response.data) {
              setUser(response.data as User);
            }
          } catch (err) {
            console.error('Failed to refresh user data:', err);
          }
        }
      }
    } catch (err) {
      console.error('Failed to initialize auth:', err);
      clearAuth();
      setUser(null);
    } finally {
      setIsInitialized(true);
    }
  }, []);

  /**
   * Login
   */
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.login(credentials.email, credentials.password);

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Login failed');
      }

      const authData = response.data as AuthResponse;

      // Store auth data
      storeAuth(authData.token, authData.user);

      // Update state
      setUser(authData.user);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Logout
   */
  const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Call logout API (don't throw on error)
      await apiClient.logout().catch((err) => {
        console.error('Logout API call failed:', err);
      });
    } finally {
      // Clear auth data regardless of API call result
      clearAuth();
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  /**
   * Refresh user data
   */
  const refreshUser = useCallback(async () => {
    if (!checkIsAuthenticated()) {
      return;
    }

    try {
      const response = await apiClient.getCurrentUser();

      if (response.success && response.data) {
        const userData = response.data as User;
        setUser(userData);

        // Update stored user
        const token = getAuthToken();
        const refreshToken = getRefreshToken();
        if (token) {
          storeAuth(
            {
              access_token: token,
              token_type: 'Bearer',
              expires_in: 3600,
              refresh_token: refreshToken || undefined,
              issued_at: Date.now(),
            },
            userData
          );
        }
      }
    } catch (err) {
      console.error('Failed to refresh user:', err);
    }
  }, []);

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Auto-refresh token if expiring soon
   */
  useEffect(() => {
    if (!user || !checkIsAuthenticated()) {
      return;
    }

    const token = getAuthToken();
    if (!token) {
      return;
    }

    // Check every minute if token needs refresh
    const interval = setInterval(async () => {
      if (isTokenExpiringSoon(token)) {
        const refreshToken = getRefreshToken();
        if (refreshToken) {
          try {
            const response = await apiClient.refreshToken(refreshToken);
            if (response.success && response.data) {
              const authData = response.data as AuthResponse;
              storeAuth(authData.token, authData.user);
              setUser(authData.user);
            }
          } catch (err) {
            console.error('Failed to refresh token:', err);
            // If refresh fails, logout
            await logout();
          }
        }
      }
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [user, logout]);

  /**
   * Initialize on mount
   */
  useEffect(() => {
    initialize();
  }, [initialize]);

  /**
   * Context value
   */
  const value: AuthContextState = {
    user,
    isAuthenticated: !!user && checkIsAuthenticated(),
    isLoading,
    isInitialized,
    error,
    login,
    logout,
    refreshUser,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthProvider;
