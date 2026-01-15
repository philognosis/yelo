/**
 * User Types
 * Authentication and authorization types
 */

/**
 * User Role
 * Defines the role-based access control levels
 */
export enum UserRole {
  ADMIN = 'admin',
  EVALUATOR = 'evaluator',
  ANALYST = 'analyst',
  VIEWER = 'viewer',
}

/**
 * Permission
 * Granular permissions for different actions
 */
export enum Permission {
  // Evaluation permissions
  CREATE_EVALUATION = 'create_evaluation',
  VIEW_EVALUATION = 'view_evaluation',
  UPDATE_EVALUATION = 'update_evaluation',
  DELETE_EVALUATION = 'delete_evaluation',

  // Rating permissions
  CREATE_RATING = 'create_rating',
  VIEW_RATING = 'view_rating',
  UPDATE_RATING = 'update_rating',

  // Analysis permissions
  VIEW_ANALYSIS = 'view_analysis',
  EXPORT_ANALYSIS = 'export_analysis',

  // User management
  MANAGE_USERS = 'manage_users',
  VIEW_USERS = 'view_users',

  // System
  VIEW_METRICS = 'view_metrics',
  MANAGE_SETTINGS = 'manage_settings',
  VIEW_LOGS = 'view_logs',
}

/**
 * User Preferences
 * User-specific settings and preferences
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    evaluation_complete: boolean;
    evaluation_failed: boolean;
    weekly_summary: boolean;
  };
  dashboard: {
    default_view: 'grid' | 'list' | 'kanban';
    items_per_page: number;
    show_archived: boolean;
  };
}

/**
 * User Profile
 * Extended user information
 */
export interface UserProfile {
  bio?: string;
  avatar_url?: string;
  department?: string;
  job_title?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
}

/**
 * User
 * Complete user object
 */
export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;

  // Authentication
  email_verified: boolean;
  is_active: boolean;
  is_locked: boolean;

  // Authorization
  role: UserRole;
  permissions: Permission[];

  // Profile
  profile?: UserProfile;
  preferences: UserPreferences;

  // Metadata
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  login_count: number;
}

/**
 * User Summary
 * Condensed user info for lists and references
 */
export interface UserSummary {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: UserRole;
  avatar_url?: string;
  is_active: boolean;
}

/**
 * Authentication Token
 * JWT token structure
 */
export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  issued_at: number;
}

/**
 * Authentication Response
 * Response from login/registration
 */
export interface AuthResponse {
  user: User;
  token: AuthToken;
}

/**
 * Login Credentials
 * User credentials for authentication
 */
export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

/**
 * Registration Data
 * User data for registration
 */
export interface RegistrationData {
  email: string;
  username: string;
  password: string;
  full_name: string;
  accept_terms: boolean;
}

/**
 * Password Reset Request
 * Request to reset password
 */
export interface PasswordResetRequest {
  email: string;
}

/**
 * Password Reset Confirmation
 * Confirm password reset with token
 */
export interface PasswordResetConfirmation {
  token: string;
  new_password: string;
}

/**
 * User Activity
 * Track user activity for audit logs
 */
export interface UserActivity {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

/**
 * Session Info
 * Information about the current session
 */
export interface SessionInfo {
  id: string;
  user_id: string;
  ip_address: string;
  user_agent: string;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  is_current: boolean;
}

/**
 * Role Permissions Map
 * Defines which permissions each role has
 */
export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  [UserRole.ADMIN]: Object.values(Permission),
  [UserRole.EVALUATOR]: [
    Permission.CREATE_EVALUATION,
    Permission.VIEW_EVALUATION,
    Permission.UPDATE_EVALUATION,
    Permission.CREATE_RATING,
    Permission.VIEW_RATING,
    Permission.UPDATE_RATING,
    Permission.VIEW_ANALYSIS,
    Permission.VIEW_METRICS,
  ],
  [UserRole.ANALYST]: [
    Permission.VIEW_EVALUATION,
    Permission.VIEW_RATING,
    Permission.VIEW_ANALYSIS,
    Permission.EXPORT_ANALYSIS,
    Permission.VIEW_METRICS,
  ],
  [UserRole.VIEWER]: [
    Permission.VIEW_EVALUATION,
    Permission.VIEW_RATING,
    Permission.VIEW_ANALYSIS,
    Permission.VIEW_METRICS,
  ],
};
