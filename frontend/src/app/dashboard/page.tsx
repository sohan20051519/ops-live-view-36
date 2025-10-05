'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import NewProjectForm from '@/components/dashboard/NewProjectForm';

export default function DashboardPage() {
  const { session, logout, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !session) {
      router.push('/login');
    }
  }, [session, loading, router]);

  if (loading || !session) {
    // You can render a loading spinner here
    return <p>Loading...</p>;
  }

  return (
    <div className="flex flex-col items-center justify-start min-h-screen bg-gray-100 dark:bg-gray-900 py-12">
      <div className="w-full max-w-4xl px-4">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Welcome to Devyntra</h1>
            <p className="text-muted-foreground">Logged in as {session.user.email}</p>
          </div>
          <Button onClick={logout} variant="outline">
            Logout
          </Button>
        </div>

        <NewProjectForm />

        <ProjectList />
      </div>
    </div>
  );
}