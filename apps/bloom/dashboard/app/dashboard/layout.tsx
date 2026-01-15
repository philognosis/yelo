'use client';

import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout as Layout } from '../../components/DashboardLayout';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

/**
 * Dashboard layout wrapper
 * Provides the common dashboard shell with sidebar and header
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <Layout>{children}</Layout>;
}
