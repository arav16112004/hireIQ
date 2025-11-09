"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from './api';
import { useRouter } from 'next/navigation';

interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  company_name?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string, redirectUrl?: string) => Promise<User>;
  register: (email: string, password: string, name: string, role?: string, company_name?: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check for existing token
    const savedToken = localStorage.getItem('token');
    console.log('Auth context initializing - token exists:', !!savedToken);
    if (savedToken) {
      setToken(savedToken);
      fetchUser();
    } else {
      console.log('No saved token found');
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      console.log('Fetching user profile...');
      const response = await apiClient.auth.me();
      console.log('User profile loaded:', response.data);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string, redirectUrl?: string): Promise<User> => {
    try {
      console.log('Attempting login for:', email);
      console.log('Redirect URL provided:', redirectUrl);
      const response = await apiClient.auth.login(email, password);
      
      console.log('Login response:', response.data);
      
      const accessToken = response.data.access_token;
      const userData = response.data.user;
      
      if (!accessToken) {
        throw new Error('No access token received');
      }
      
      console.log('Setting token in localStorage');
      localStorage.setItem('token', accessToken);
      setToken(accessToken);
      setUser(userData);
      console.log('Token set, user data:', userData);
      
      // Small delay to ensure token is stored before navigation
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Return user data so caller can handle redirect
      console.log('Login successful - returning user data');
      return userData;
    } catch (error: any) {
      console.error('Login error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      throw new Error(errorMessage);
    }
  };

  const register = async (email: string, password: string, name: string, role: string = 'candidate', company_name?: string) => {
    try {
      const response = await apiClient.auth.register({ email, password, name, role, company_name });
      
      // Check response structure
      console.log('Register response:', response.data);
      
      const accessToken = response.data.access_token;
      const userData = response.data.user;
      
      if (!accessToken) {
        throw new Error('No access token received');
      }
      
      localStorage.setItem('token', accessToken);
      setToken(accessToken);
      setUser(userData);
      
      // Redirect to profile completion
      if (role === 'candidate') {
        router.push('/candidate/profile');
      } else {
        router.push('/recruiter/dashboard');
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed';
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    router.push('/');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
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

