'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Github, Mail, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { supabase } from '@/lib/supabaseClient';

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user: {
    id: string;
    email: string;
    user_metadata?: any;
  };
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<'google' | 'github' | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please enter email and password');
      return;
    }

    try {
      setLoading(true);
      const response = await api.post<LoginResponse>('/v1/auth/login/', {
        email,
        password,
      });

      // Store token in localStorage
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        // Store user info
        localStorage.setItem('user', JSON.stringify(response.user));
        
        toast.success('Login successful!');
        router.push('/dashboard');
      } else {
        toast.error('Login failed: No token received');
      }
    } catch (error: any) {
      console.error('Login failed:', error);
      toast.error(error?.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider: 'google' | 'github') => {
    try {
      setOauthLoading(provider);
      const redirectTo = typeof window !== 'undefined'
        ? `${window.location.origin}/auth/callback`
        : undefined;

      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo,
        },
      });

      if (error) {
        throw error;
      }
    } catch (error: any) {
      console.error(`${provider} login failed:`, error);
      toast.error(error?.message || 'Login failed. Please try again.');
      setOauthLoading(null);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-md mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card>
                <CardHeader className="text-center">
                  <CardTitle className="text-3xl mb-2">Welcome Back</CardTitle>
                  <CardDescription>
                    Sign in to your account to continue building your resume
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="you@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        disabled={loading}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="password">Password</Label>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="text-sm text-primary hover:underline h-auto p-0"
                        onClick={(e) => {
                          e.preventDefault();
                          // TODO: Add password reset functionality
                          toast.info('Password reset coming soon');
                        }}
                      >
                        Forgot?
                      </Button>
                      </div>
                      <Input
                        id="password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={loading}
                      />
                    </div>
                    <Button
                      type="submit"
                      className="w-full bg-gradient-to-r from-primary to-secondary"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Signing in...
                        </>
                      ) : (
                        'Sign In'
                      )}
                    </Button>
                  </form>
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Button
                      variant="outline"
                      className="w-full"
                      disabled={oauthLoading !== null}
                      onClick={() => handleOAuth('github')}
                    >
                      {oauthLoading === 'github' ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                      <Github className="mr-2 h-4 w-4" />
                      )}
                      GitHub
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full"
                      disabled={oauthLoading !== null}
                      onClick={() => handleOAuth('google')}
                    >
                      {oauthLoading === 'google' ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                      <Mail className="mr-2 h-4 w-4" />
                      )}
                      Google
                    </Button>
                  </div>
                  <div className="text-center text-sm text-muted-foreground">
                    Don&apos;t have an account?{' '}
                    <Link href="/register" className="text-primary hover:underline">
                      Sign up
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}


