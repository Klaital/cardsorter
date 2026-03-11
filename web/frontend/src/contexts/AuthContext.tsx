import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { setApiToken } from '../lib/api';

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => {
    // Load token from localStorage and immediately set it on the API client
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
      setApiToken(savedToken);
    }
    return savedToken;
  });

  useEffect(() => {
    // Keep localStorage in sync when token changes
    if (token) {
      localStorage.setItem('authToken', token);
      setApiToken(token);
    } else {
      localStorage.removeItem('authToken');
      setApiToken(undefined);
    }
  }, [token]);

  const login = (newToken: string) => {
    setToken(newToken);
  };

  const logout = () => {
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: !!token,
        login,
        logout,
      }}
    >
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
