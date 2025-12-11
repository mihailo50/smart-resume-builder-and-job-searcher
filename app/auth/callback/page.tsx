'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';
import { toast } from 'sonner';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('Finishing sign in...');

  useEffect(() => {
    const finishSignIn = async () => {
      const errorDescription = searchParams.get('error_description') || searchParams.get('error');
      if (errorDescription) {
        toast.error(errorDescription);
        router.replace('/login');
        return;
      }

      const { data, error } = await supabase.auth.getSession();
      if (error || !data.session) {
        toast.error('No session returned from Supabase. Please try again.');
        router.replace('/login');
        return;
      }

      const { access_token, refresh_token, user } = data.session;
      localStorage.setItem('auth_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }
      localStorage.setItem('user', JSON.stringify(user));

      setStatus('Redirecting...');
      router.replace('/dashboard');
    };

    finishSignIn();
  }, [router, searchParams]);

  return (
    <div className="flex items-center space-x-3 text-muted-foreground">
      <Loader2 className="h-5 w-5 animate-spin" />
      <span>{status}</span>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-primary/5">
      <Suspense fallback={
        <div className="flex items-center space-x-3 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading...</span>
        </div>
      }>
        <AuthCallbackContent />
      </Suspense>
    </div>
  );
}
