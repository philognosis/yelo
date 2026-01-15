/**
 * Theme Context
 * Provides theme state and actions (light/dark mode)
 */

'use client';

import React, { createContext, useState, useEffect, useCallback, ReactNode, useContext } from 'react';

/**
 * Theme Type
 */
export type Theme = 'light' | 'dark' | 'auto';

/**
 * Resolved Theme (actual theme being used)
 */
export type ResolvedTheme = 'light' | 'dark';

/**
 * Theme Context State
 */
interface ThemeContextState {
  // Current theme setting
  theme: Theme;

  // Resolved theme (what's actually applied)
  resolvedTheme: ResolvedTheme;

  // System preference
  systemTheme: ResolvedTheme;

  // Actions
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

/**
 * Create context with undefined default
 */
export const ThemeContext = createContext<ThemeContextState | undefined>(undefined);

/**
 * Provider Props
 */
interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
}

/**
 * Storage key for theme preference
 */
const DEFAULT_STORAGE_KEY = 'bloom_theme';

/**
 * Theme Provider Component
 * Manages theme state and applies theme to document
 */
export function ThemeProvider({
  children,
  defaultTheme = 'auto',
  storageKey = DEFAULT_STORAGE_KEY,
}: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>('light');
  const [mounted, setMounted] = useState(false);

  /**
   * Get resolved theme based on current theme and system preference
   */
  const getResolvedTheme = useCallback(
    (themeValue: Theme): ResolvedTheme => {
      if (themeValue === 'auto') {
        return systemTheme;
      }
      return themeValue;
    },
    [systemTheme]
  );

  const resolvedTheme = getResolvedTheme(theme);

  /**
   * Detect system theme preference
   */
  const detectSystemTheme = useCallback((): ResolvedTheme => {
    if (typeof window === 'undefined') {
      return 'light';
    }

    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return isDark ? 'dark' : 'light';
  }, []);

  /**
   * Set theme and persist to storage
   */
  const setTheme = useCallback(
    (newTheme: Theme) => {
      setThemeState(newTheme);

      // Persist to storage
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem(storageKey, newTheme);
        } catch (err) {
          console.error('Failed to save theme preference:', err);
        }
      }
    },
    [storageKey]
  );

  /**
   * Toggle between light and dark
   */
  const toggleTheme = useCallback(() => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  }, [resolvedTheme, setTheme]);

  /**
   * Apply theme to document
   */
  const applyTheme = useCallback((themeToApply: ResolvedTheme) => {
    if (typeof document === 'undefined') {
      return;
    }

    const root = document.documentElement;

    // Remove previous theme
    root.classList.remove('light', 'dark');

    // Add new theme
    root.classList.add(themeToApply);

    // Set color-scheme for native elements
    root.style.colorScheme = themeToApply;

    // Update meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      const color = themeToApply === 'dark' ? '#111827' : '#ffffff';
      metaThemeColor.setAttribute('content', color);
    }
  }, []);

  /**
   * Initialize theme from storage
   */
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    // Detect system theme
    const detectedSystemTheme = detectSystemTheme();
    setSystemTheme(detectedSystemTheme);

    // Load theme from storage
    try {
      const storedTheme = localStorage.getItem(storageKey);
      if (storedTheme && ['light', 'dark', 'auto'].includes(storedTheme)) {
        setThemeState(storedTheme as Theme);
      }
    } catch (err) {
      console.error('Failed to load theme preference:', err);
    }

    setMounted(true);
  }, [detectSystemTheme, storageKey]);

  /**
   * Listen for system theme changes
   */
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      const newSystemTheme = e.matches ? 'dark' : 'light';
      setSystemTheme(newSystemTheme);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
    // Legacy browsers
    else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, []);

  /**
   * Apply theme when it changes
   */
  useEffect(() => {
    if (mounted) {
      applyTheme(resolvedTheme);
    }
  }, [resolvedTheme, mounted, applyTheme]);

  /**
   * Context value
   */
  const value: ThemeContextState = {
    theme,
    resolvedTheme,
    systemTheme,
    setTheme,
    toggleTheme,
  };

  // Don't render children until mounted to avoid hydration mismatch
  if (!mounted) {
    return null;
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Hook for accessing theme context
 */
export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}

export default ThemeProvider;
