'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import LoadingSpinner from '@/components/LoadingSpinner';

/**
 * Landing page with role-based redirect
 * Automatically redirects authenticated users to their role-specific dashboard
 */
export default function HomePage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (!user) {
      router.push('/login');
      return;
    }

    // Redirect to role-specific dashboard
    switch (user.role) {
      case 'employee':
        router.push('/employee');
        break;
      case 'manager':
        router.push('/manager');
        break;
      case 'hr_admin':
        router.push('/hr');
        break;
      case 'committee':
        router.push('/committee');
        break;
      default:
        router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <LoadingSpinner size="xl" />
    </div>
  );
}
