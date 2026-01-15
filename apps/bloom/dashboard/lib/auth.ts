/**
 * Authentication Utilities
 * JWT token management and role-based access control
 */

import { User, UserRole, Permission, ROLE_PERMISSIONS } from '@/types/user';
import { AuthToken } from '@/types/user';

// Storage keys
const AUTH_TOKEN_KEY = 'bloom_auth_token';
const REFRESH_TOKEN_KEY = 'bloom_refresh_token';
const USER_KEY = 'bloom_user';

/**
 * Get auth token from storage
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Get refresh token from storage
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Get user from storage
 */
export function getStoredUser(): User | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) {
    return null;
  }

  try {
    return JSON.parse(userStr) as User;
  } catch (error) {
    console.error('Failed to parse stored user:', error);
    return null;
  }
}

/**
 * Store auth data
 */
export function storeAuth(token: AuthToken, user: User): void {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.setItem(AUTH_TOKEN_KEY, token.access_token);
  if (token.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token.refresh_token);
  }
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Clear auth data
 */
export function clearAuth(): void {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const token = getAuthToken();
  if (!token) {
    return false;
  }

  // Check if token is expired
  try {
    const payload = parseJWT(token);
    if (!payload.exp) {
      return false;
    }

    const now = Date.now() / 1000;
    return payload.exp > now;
  } catch (error) {
    console.error('Failed to parse JWT:', error);
    return false;
  }
}

/**
 * Parse JWT token
 */
export function parseJWT(token: string): Record<string, unknown> {
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) {
      throw new Error('Invalid token format');
    }

    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );

    return JSON.parse(jsonPayload) as Record<string, unknown>;
  } catch (error) {
    throw new Error('Failed to parse JWT token');
  }
}

/**
 * Get token expiration date
 */
export function getTokenExpiration(token: string): Date | null {
  try {
    const payload = parseJWT(token);
    if (!payload.exp || typeof payload.exp !== 'number') {
      return null;
    }
    return new Date(payload.exp * 1000);
  } catch (error) {
    return null;
  }
}

/**
 * Check if token is about to expire (within 5 minutes)
 */
export function isTokenExpiringSoon(token: string): boolean {
  const expiration = getTokenExpiration(token);
  if (!expiration) {
    return true;
  }

  const now = Date.now();
  const fiveMinutes = 5 * 60 * 1000;
  return expiration.getTime() - now < fiveMinutes;
}

// ==================== Authorization ====================

/**
 * Check if user has a specific role
 */
export function hasRole(user: User | null, role: UserRole): boolean {
  if (!user) {
    return false;
  }
  return user.role === role;
}

/**
 * Check if user has any of the specified roles
 */
export function hasAnyRole(user: User | null, roles: UserRole[]): boolean {
  if (!user) {
    return false;
  }
  return roles.includes(user.role);
}

/**
 * Check if user has a specific permission
 */
export function hasPermission(user: User | null, permission: Permission): boolean {
  if (!user) {
    return false;
  }

  // Check explicit permissions first
  if (user.permissions.includes(permission)) {
    return true;
  }

  // Check role-based permissions
  const rolePermissions = ROLE_PERMISSIONS[user.role];
  return rolePermissions.includes(permission);
}

/**
 * Check if user has all specified permissions
 */
export function hasAllPermissions(user: User | null, permissions: Permission[]): boolean {
  if (!user) {
    return false;
  }
  return permissions.every((permission) => hasPermission(user, permission));
}

/**
 * Check if user has any of the specified permissions
 */
export function hasAnyPermission(user: User | null, permissions: Permission[]): boolean {
  if (!user) {
    return false;
  }
  return permissions.some((permission) => hasPermission(user, permission));
}

/**
 * Check if user is admin
 */
export function isAdmin(user: User | null): boolean {
  return hasRole(user, UserRole.ADMIN);
}

/**
 * Check if user can create evaluations
 */
export function canCreateEvaluation(user: User | null): boolean {
  return hasPermission(user, Permission.CREATE_EVALUATION);
}

/**
 * Check if user can view evaluation
 */
export function canViewEvaluation(user: User | null): boolean {
  return hasPermission(user, Permission.VIEW_EVALUATION);
}

/**
 * Check if user can update evaluation
 */
export function canUpdateEvaluation(user: User | null): boolean {
  return hasPermission(user, Permission.UPDATE_EVALUATION);
}

/**
 * Check if user can delete evaluation
 */
export function canDeleteEvaluation(user: User | null): boolean {
  return hasPermission(user, Permission.DELETE_EVALUATION);
}

/**
 * Check if user can export data
 */
export function canExportData(user: User | null): boolean {
  return hasPermission(user, Permission.EXPORT_ANALYSIS);
}

/**
 * Check if user can manage users
 */
export function canManageUsers(user: User | null): boolean {
  return hasPermission(user, Permission.MANAGE_USERS);
}

/**
 * Get user's full permissions list
 */
export function getUserPermissions(user: User | null): Permission[] {
  if (!user) {
    return [];
  }

  // Combine explicit permissions and role-based permissions
  const rolePermissions = ROLE_PERMISSIONS[user.role];
  const allPermissions = [...new Set([...user.permissions, ...rolePermissions])];
  return allPermissions;
}

/**
 * Format permission name for display
 */
export function formatPermission(permission: Permission): string {
  return permission
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Format role name for display
 */
export function formatRole(role: UserRole): string {
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase();
}
