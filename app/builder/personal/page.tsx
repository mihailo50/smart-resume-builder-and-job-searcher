'use client';

import { useState, useEffect, Suspense } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { useGuestGuard } from '@/lib/use-guest-guard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, ArrowRight, ArrowLeft, Sparkles, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { 
  isAuthenticated, 
  saveGuestResume, 
  loadGuestResume, 
  getGuestResumeId 
} from '@/lib/guest-resume';
import { useDirtyGuard, useBeforeUnloadGuard, clearDirtyState } from '@/lib/use-dirty-guard';

const personalSchema = z.object({
  fullName: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  phone: z.string().min(10, 'Invalid phone number'),
  location: z.string().optional(),
  dateOfBirth: z.string().optional(),
  avatarUrl: z.string().url('Invalid URL').optional().or(z.literal('')),
  linkedin: z.string().url('Invalid URL').optional().or(z.literal('')),
  github: z.string().url('Invalid URL').optional().or(z.literal('')),
  portfolio: z.string().url('Invalid URL').optional().or(z.literal('')),
});

type PersonalFormData = z.infer<typeof personalSchema>;

function PersonalInfoContent() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [progress, setProgress] = useState(11); // Step 1 of 9
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
    reset,
  } = useForm<PersonalFormData>({
    resolver: zodResolver(personalSchema),
    defaultValues: {
      fullName: '',
      email: '',
      phone: '',
      location: '',
      dateOfBirth: '',
      avatarUrl: '',
      linkedin: '',
      github: '',
      portfolio: '',
    },
  });

  // Track dirty state for beforeunload guard
  useDirtyGuard(isDirty, 'personal');
  useBeforeUnloadGuard(!isAuthenticated()); // Only for guest users

  // Load existing resume data if editing
  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    const loadData = async () => {
      if (guestId || (!resumeId && !isAuthenticated())) {
        // Guest mode - load from localStorage
        loadGuestData();
      } else if (resumeId && isAuthenticated()) {
        // Authenticated mode - load from API
        await loadResumeData();
      } else {
        // No resumeId and not authenticated - try loading guest data
        loadGuestData();
      }
    };
    
    loadData();
  }, [resumeId, searchParams]);

  const loadResumeData = async () => {
    try {
      setLoading(true);
      console.log('[PERSONAL PAGE] Loading resume data for ID:', resumeId);
      
      // Get resume with details
      const resume = await api.get<any>(`/v1/resumes/${resumeId}/`);
      console.log('[PERSONAL PAGE] Resume data received:', resume);
      
      // Personal info (email, phone, etc.) might be in user_profiles
      // For now, load what we can from the resume
      // The title is the full_name
      reset({
        fullName: resume.title || '',
        email: '', // Will be loaded from user profile if available
        phone: '', // Will be loaded from user profile if available
        location: '', // Will be loaded from user profile if available
        linkedin: '', // Will be loaded from user profile if available
        github: '', // Will be loaded from user profile if available
        portfolio: '', // Will be loaded from user profile if available
      });
      
      // Try to load user info from auth endpoint
      try {
        const userInfo = await api.get<any>('/v1/auth/me/');
        console.log('[PERSONAL PAGE] User info received:', userInfo);
        if (userInfo?.user) {
          const profile = userInfo.user.profile || {};
          reset({
            fullName: resume.title || userInfo.user.user_metadata?.full_name || '',
            email: userInfo.user.email || '',
            phone: profile.phone_number || '',
            location: profile.location || '',
            dateOfBirth: profile.date_of_birth || '',
            avatarUrl: profile.avatar || '',
            linkedin: profile.linkedin_url || '',
            github: profile.github_url || '',
            portfolio: profile.portfolio_url || '',
          });
        }
      } catch (userError) {
        console.warn('[PERSONAL PAGE] Could not load user info (this is OK if not set):', userError);
        // This is fine - user info might not be available, use what we have from resume
      }
      
      console.log('[PERSONAL PAGE] Form reset with data');
    } catch (error: any) {
      console.error('[PERSONAL PAGE] Failed to load resume:', error);
      // Fallback to guest data if API fails
      loadGuestData();
    } finally {
      setLoading(false);
    }
  };

  const loadGuestData = () => {
    try {
      const guestData = loadGuestResume();
      if (guestData.personal) {
        reset({
          fullName: guestData.personal.fullName || '',
          email: guestData.personal.email || '',
          phone: guestData.personal.phone || '',
          location: guestData.personal.location || '',
          dateOfBirth: guestData.personal.dateOfBirth || '',
          avatarUrl: guestData.personal.avatarUrl || '',
          linkedin: guestData.personal.linkedin || '',
          github: guestData.personal.github || '',
          portfolio: guestData.personal.portfolio || '',
        });
      }
    } catch (error) {
      console.error('Failed to load guest data:', error);
    }
  };

  const onSubmit = async (data: PersonalFormData) => {
    try {
      setSaving(true);
      
      // Check if user is authenticated
      if (isAuthenticated()) {
        // Authenticated flow - save to API
        let currentResumeId = resumeId;

        // Create resume if it doesn't exist
        if (!currentResumeId) {
          const newResume = await api.post('/v1/resumes/', {
            title: data.fullName || 'New Resume',
          });
          currentResumeId = newResume.id;
          toast.success('Resume created');
        }

        // Update personal info
        await api.put(`/v1/resumes/${currentResumeId}/personal/`, {
          full_name: data.fullName,
          email: data.email,
          phone: data.phone,
          location: data.location || '',
          date_of_birth: data.dateOfBirth || null,
          avatar_url: data.avatarUrl || '',
          linkedin_url: data.linkedin || '',
          github_url: data.github || '',
          portfolio_url: data.portfolio || '',
        });

        toast.success('Personal information saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/experience?id=${currentResumeId}`);
      } else {
        // Guest flow - save to localStorage
        saveGuestResume({
          personal: {
            fullName: data.fullName,
            email: data.email,
            phone: data.phone,
            location: data.location || '',
            dateOfBirth: data.dateOfBirth || '',
            avatarUrl: data.avatarUrl || '',
            linkedin: data.linkedin || '',
            github: data.github || '',
            portfolio: data.portfolio || '',
          },
        });
        
        const guestResumeId = getGuestResumeId();
        toast.success('Personal information saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/experience?guestId=${guestResumeId}`);
      }
    } catch (error: any) {
      console.error('Failed to save personal info:', error);
      toast.error(error?.message || 'Failed to save personal information');
    } finally {
      setSaving(false);
    }
  };

  const steps = [
    { id: 1, name: 'Personal Info', href: '/builder/personal', current: true },
    { id: 2, name: 'Experience', href: '/builder/experience', current: false },
    { id: 3, name: 'Projects', href: '/builder/projects', current: false },
    { id: 4, name: 'Education', href: '/builder/education', current: false },
    { id: 5, name: 'Certifications', href: '/builder/certifications', current: false },
    { id: 6, name: 'Skills', href: '/builder/skills', current: false },
    { id: 7, name: 'Languages', href: '/builder/languages', current: false },
    { id: 8, name: 'Interests', href: '/builder/interests', current: false },
    { id: 9, name: 'Summary', href: '/builder/summary', current: false },
    { id: 10, name: 'AI Optimize', href: '/builder/optimize', current: false },
    { id: 11, name: 'Preview', href: '/builder/preview', current: false },
  ];

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-6xl mx-auto">
            {/* Progress Bar */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">
                  Step {steps[0].id} of {steps.length}
                </span>
                <span className="text-sm font-medium text-muted-foreground">{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            {/* Steps Sidebar */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="lg:col-span-1"
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Resume Builder</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {steps.map((step, index) => {
                      const stepUrl = resumeId 
                        ? `${step.href}?id=${resumeId}` 
                        : guestId 
                        ? `${step.href}?guestId=${guestId}` 
                        : step.href;
                      
                      return (
                        <Link
                          key={step.id}
                          href={stepUrl}
                          className={`flex items-center gap-2 p-2 rounded-md transition-colors ${
                            step.current
                              ? 'bg-primary/10 text-primary font-semibold'
                              : 'text-muted-foreground hover:bg-accent cursor-pointer'
                          }`}
                        >
                          {index < 0 ? (
                            <CheckCircle2 className="h-4 w-4 text-primary" />
                          ) : (
                            <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary">
                              {step.id}
                            </div>
                          )}
                          <span className="text-sm">{step.name}</span>
                        </Link>
                      );
                    })}
                  </CardContent>
                </Card>
              </motion.div>

              {/* Form */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="lg:col-span-3"
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-primary" />
                      Personal Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="fullName">
                            Full Name <span className="text-destructive">*</span>
                          </Label>
                          <Input
                            id="fullName"
                            placeholder="John Doe"
                            {...register('fullName')}
                            className={errors.fullName ? 'border-destructive' : ''}
                          />
                          {errors.fullName && (
                            <p className="text-sm text-destructive">{errors.fullName.message}</p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="email">
                            Email <span className="text-destructive">*</span>
                          </Label>
                          <Input
                            id="email"
                            type="email"
                            placeholder="john@example.com"
                            {...register('email')}
                            className={errors.email ? 'border-destructive' : ''}
                          />
                          {errors.email && (
                            <p className="text-sm text-destructive">{errors.email.message}</p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="phone">
                            Phone <span className="text-destructive">*</span>
                          </Label>
                          <Input
                            id="phone"
                            type="tel"
                            placeholder="+1 (555) 123-4567"
                            {...register('phone')}
                            className={errors.phone ? 'border-destructive' : ''}
                          />
                          {errors.phone && (
                            <p className="text-sm text-destructive">{errors.phone.message}</p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="location">Location</Label>
                          <Input
                            id="location"
                            placeholder="New York, NY"
                            {...register('location')}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="dateOfBirth">Date of Birth</Label>
                          <Input
                            id="dateOfBirth"
                            type="date"
                            {...register('dateOfBirth')}
                          />
                        </div>

                        <div className="space-y-2 md:col-span-2">
                          <Label htmlFor="avatarUrl">Profile Photo URL</Label>
                          <Input
                            id="avatarUrl"
                            type="url"
                            placeholder="https://example.com/your-photo.jpg"
                            {...register('avatarUrl')}
                          />
                          {errors.avatarUrl && (
                            <p className="text-sm text-destructive">{errors.avatarUrl.message}</p>
                          )}
                          <p className="text-xs text-muted-foreground">
                            Paste a URL to your profile photo (e.g., from LinkedIn, GitHub, or any image hosting service)
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="linkedin">LinkedIn URL</Label>
                          <Input
                            id="linkedin"
                            type="url"
                            placeholder="https://linkedin.com/in/johndoe"
                            {...register('linkedin')}
                          />
                          {errors.linkedin && (
                            <p className="text-sm text-destructive">{errors.linkedin.message}</p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="github">GitHub URL</Label>
                          <Input
                            id="github"
                            type="url"
                            placeholder="https://github.com/johndoe"
                            {...register('github')}
                          />
                          {errors.github && (
                            <p className="text-sm text-destructive">{errors.github.message}</p>
                          )}
                        </div>

                        <div className="space-y-2 md:col-span-2">
                          <Label htmlFor="portfolio">Portfolio URL</Label>
                          <Input
                            id="portfolio"
                            type="url"
                            placeholder="https://johndoe.com"
                            {...register('portfolio')}
                          />
                          {errors.portfolio && (
                            <p className="text-sm text-destructive">{errors.portfolio.message}</p>
                          )}
                        </div>
                      </div>

                      <div className="flex justify-between pt-4">
                        <Button type="button" variant="outline" asChild>
                          <Link href="/builder">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back
                          </Link>
                        </Button>
                        <Button
                          type="submit"
                          disabled={isSubmitting || saving || loading}
                          className="bg-gradient-to-r from-primary to-secondary"
                        >
                          {saving || loading ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              {loading ? 'Loading...' : 'Saving...'}
                            </>
                          ) : (
                            <>
                              Next: Experience
                              <ArrowRight className="ml-2 h-4 w-4" />
                            </>
                          )}
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}

export default function PersonalInfoPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <PersonalInfoContent />
    </Suspense>
  );
}
