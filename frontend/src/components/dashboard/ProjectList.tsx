'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface Project {
  id: string;
  name: string;
  repo_url: string;
  status: string;
  language?: string;
}

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { session } = useAuth();

  const fetchProjects = async () => {
    if (!session) return;

    try {
      const response = await fetch('http://localhost:8000/projects', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch projects');
      }

      const data = await response.json();
      setProjects(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();

    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      fetchProjects();
    }, 5000);

    return () => clearInterval(interval);
  }, [session]);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'ready_to_deploy':
        return 'success';
      case 'analysis_pending':
        return 'secondary';
      case 'analysis_failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return <p>Loading projects...</p>;
  }

  if (error) {
    return <p className="text-red-500">Error: {error}</p>;
  }

  return (
    <div className="mt-12">
      <h2 className="text-2xl font-bold mb-4">Your Projects</h2>
      {projects.length === 0 ? (
        <div className="p-8 border-2 border-dashed rounded-lg text-center text-muted-foreground">
          <p>You haven't created any projects yet. Add one above to get started.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {projects.map((project) => (
            <Card key={project.id}>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>{project.name}</CardTitle>
                <Badge variant={getStatusBadgeVariant(project.status)}>
                  {project.status.replace(/_/g, ' ')}
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-2">{project.repo_url}</p>
                {project.language && <p>Language: {project.language}</p>}
                 {project.status === 'ready_to_deploy' && (
                    <Button className="mt-4">Deploy Project</Button>
                 )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}