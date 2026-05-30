'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { get } from "@/lib/api-client";

interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "reviewer" | "practitioner";
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  isLoading: true,
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch current user profile using the stored token
  const fetchUser = useCallback(async (storedToken: string) => {
    try {
      const profile = await get<User>("/api/auth/me");
      setUser(profile);
      setToken(storedToken);
    } catch {
      localStorage.removeItem("access_token");
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    if (storedToken) {
      fetchUser(storedToken);
    } else {
      setIsLoading(false);
    }
  }, [fetchUser]);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    setUser(null);
    setToken(null);
    window.location.href = "/login";
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}
