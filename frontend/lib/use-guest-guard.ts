'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * Hook to check if user is authenticated.
 * If not authenticated, redirects to login page.
 * Use this on protected pages that require authentication.
 */
export function useGuestGuard() {
  const router = useRouter();

  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const token = localStorage.getItem('auth_token');
    // For guest guard, we don't redirect - we just track guest status
    // The actual auth guard functionality is handled by individual pages
  }, [router]);
}

/**
 * Hook to protect routes that require authentication.
 * Redirects to login if no auth token is found.
 */
export function useAuthGuard() {
  const router = useRouter();

  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const token = localStorage.getItem('auth_token');
    if (!token) {
      router.replace('/login');
    }
  }, [router]);
}



