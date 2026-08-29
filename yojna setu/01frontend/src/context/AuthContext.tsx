import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, LoginRequest, RegisterRequest, UserRole, TokenResponse } from '../types';
import { authApi } from '../api/authApi';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  role: UserRole | null;
  login: (credentials: LoginRequest) => Promise<TokenResponse>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('yojnasetu_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('yojnasetu_access_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    if (!localStorage.getItem('yojnasetu_access_token')) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await authApi.getMe();
      setUser(me);
      localStorage.setItem('yojnasetu_user', JSON.stringify(me));
    } catch (err) {
      console.error("Failed to load active user:", err);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
    setIsLoading(true);
    try {
      const res = await authApi.login(credentials);
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem('yojnasetu_access_token', res.access_token);
      localStorage.setItem('yojnasetu_user', JSON.stringify(res.user));
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterRequest) => {
    setIsLoading(true);
    try {
      await authApi.register(payload);
      const identifier = payload.email || payload.phone || '';
      const loginRes = await authApi.login({ identifier, password: payload.password });
      setToken(loginRes.access_token);
      setUser(loginRes.user);
      localStorage.setItem('yojnasetu_access_token', loginRes.access_token);
      localStorage.setItem('yojnasetu_user', JSON.stringify(loginRes.user));
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('yojnasetu_access_token');
    localStorage.removeItem('yojnasetu_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
        role: user ? user.role : null,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
