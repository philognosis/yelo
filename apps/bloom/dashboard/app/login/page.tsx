'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { Card } from '../../components/Card';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const demoRoles = [
    { role: 'employee', name: 'Employee', email: 'employee@example.com', description: 'View and complete evaluations' },
    { role: 'manager', name: 'Manager', email: 'manager@example.com', description: 'Manage team evaluations with AI assistance' },
    { role: 'hr_admin', name: 'HR Admin', email: 'hr@example.com', description: 'Oversee cycles and system settings' },
    { role: 'committee', name: 'Committee', email: 'committee@example.com', description: 'Review and calibrate evaluations' },
  ];

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, 'demo-password');
      router.push('/');
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (demoEmail: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await login(demoEmail, 'demo-password');
      router.push('/');
    } catch (err) {
      setError('Demo login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Welcome to Bloom</h1>
          <p className="text-lg text-gray-600">AI-Powered Performance Evaluation System</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Login Form */}
          <Card className="p-6">
            <h2 className="text-2xl font-semibold mb-6">Sign In</h2>

            <form onSubmit={handleLogin} className="space-y-4">
              <Input
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                disabled={isLoading}
              />

              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                required
                disabled={isLoading}
              />

              {error && (
                <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                variant="primary"
                fullWidth
                isLoading={isLoading}
              >
                Sign In
              </Button>
            </form>
          </Card>

          {/* Demo Roles */}
          <Card className="p-6">
            <h2 className="text-2xl font-semibold mb-6">Demo Accounts</h2>

            <div className="space-y-3">
              {demoRoles.map((demo) => (
                <button
                  key={demo.role}
                  onClick={() => handleDemoLogin(demo.email)}
                  disabled={isLoading}
                  className="w-full text-left p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="font-semibold text-gray-900">{demo.name}</div>
                  <div className="text-sm text-gray-600 mt-1">{demo.description}</div>
                  <div className="text-xs text-gray-500 mt-2">{demo.email}</div>
                </button>
              ))}
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Demo Mode:</strong> Click any role above to explore the system from different perspectives.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
