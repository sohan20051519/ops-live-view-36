'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  full_name: string;
}

interface Session {
  access_token: string;
  user: User;
}

interface AuthContextType {
  session: Session | null;
  login: (sessionData: Session) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check for a session in localStorage on initial load
    const storedSession = localStorage.getItem('session');
    if (storedSession) {
      setSession(JSON.parse(storedSession));
    }
    setLoading(false);
  }, []);

  const login = (sessionData: Session) => {
    setSession(sessionData);
    localStorage.setItem('session', JSON.stringify(sessionData));
    router.push('/dashboard');
  };

  const logout = () => {
    setSession(null);
    localStorage.removeItem('session');
    router.push('/login');
  };

  const value = { session, login, logout, loading };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}