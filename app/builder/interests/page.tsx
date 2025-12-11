'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { useGuestGuard } from '@/lib/use-guest-guard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { ArrowRight, ArrowLeft, Plus, X, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { 
  isAuthenticated, 
  saveGuestResume, 
  loadGuestResume, 
  getGuestResumeId 
} from '@/lib/guest-resume';
import { useManualDirtyGuard, useBeforeUnloadGuard, clearDirtyState } from '@/lib/use-dirty-guard';

interface Interest {
  id: string;
  name: string;
}

export default function InterestsPage() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [interests, setInterests] = useState<Interest[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState(91); // Step 8 of 11
  const [initialInterests, setInitialInterests] = useState<Interest[]>([]);
  
  // Track dirty state
  const { markDirty, markClean } = useManualDirtyGuard('interests');
  useBeforeUnloadGuard(!isAuthenticated()); // Only for guest users

  // Track changes to interests array
  useEffect(() => {
    if (initialInterests.length === 0 && interests.length === 0) return;
    
    const isDirty = JSON.stringify(interests) !== JSON.stringify(initialInterests);
    if (isDirty) {
      markDirty();
    } else {
      markClean();
    }
  }, [interests, initialInterests, markDirty, markClean]);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    if (guestId || (!resumeId && !isAuthenticated())) {
      // Guest mode - load from localStorage
      loadGuestInterests();
    } else if (resumeId && isAuthenticated()) {
      // Authenticated mode - load from API
      loadInterests();
    }
  }, [resumeId, guestId]);

  const loadInterests = async () => {
    if (!resumeId) return;
    
    try {
      setLoading(true);
      const data = await api.get<any[]>(`/v1/resumes/${resumeId}/interests/`);
      const loadedInterests = data.map((int: any) => ({
        id: int.id,
        name: int.name || '',
      }));
      setInterests(loadedInterests);
      setInitialInterests(JSON.parse(JSON.stringify(loadedInterests))); // Deep copy
    } catch (error: any) {
      console.error('Failed to load interests:', error);
      toast.error('Failed to load interests');
    } finally {
      setLoading(false);
    }
  };

  const loadGuestInterests = () => {
    try {
      const guestData = loadGuestResume();
      if (guestData.interests && guestData.interests.length > 0) {
        const loadedInterests = guestData.interests.map((int: any) => ({
          id: int.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
          name: int.name || '',
        }));
        setInterests(loadedInterests);
        setInitialInterests(JSON.parse(JSON.stringify(loadedInterests))); // Deep copy
      }
    } catch (error) {
      console.error('Failed to load guest interests:', error);
    }
  };

  const addInterest = () => {
    setInterests([
      ...interests,
      {
        id: Date.now().toString(),
        name: '',
      },
    ]);
  };

  const removeInterest = (id: string) => {
    setInterests(interests.filter((int) => int.id !== id));
  };

  const updateInterest = (id: string, field: keyof Interest, value: string) => {
    setInterests(
      interests.map((int) => (int.id === id ? { ...int, [field]: value } : int))
    );
  };

  const saveInterestsToAPI = async () => {
    if (!resumeId) return;
    
    // Get existing interests from backend
    const existingInterests = await api.get(`/v1/resumes/${resumeId}/interests/`);
    const existingIds = new Set(existingInterests.map((int: any) => int.id));

    // Save/update each interest
    for (const int of interests) {
      if (!int.name.trim()) continue; // Skip empty names
      
      const interestData: Record<string, any> = {
        name: int.name.trim(),
        order: interests.indexOf(int),
      };
      
      if (int.id && existingIds.has(int.id)) {
        // Update existing
        await api.put(`/v1/resumes/${resumeId}/interests/${int.id}/`, interestData);
      } else {
        // Create new
        await api.post(`/v1/resumes/${resumeId}/interests/`, interestData);
      }
    }

    // Delete removed interests
    for (const existing of existingInterests) {
      if (!interests.some((int) => int.id === existing.id)) {
        await api.delete(`/v1/resumes/${resumeId}/interests/${existing.id}/`);
      }
    }
  };

  const handleNext = async () => {
    try {
      setSaving(true);

      if (guestId || (!resumeId && !isAuthenticated())) {
        // Guest flow - save to localStorage
        saveGuestResume({
          interests: interests
            .filter((int) => int.name.trim()) // Only save non-empty
            .map((int, index) => ({
              id: int.id,
              name: int.name.trim(),
              order: index,
            })),
        });
        
        const currentGuestId = getGuestResumeId();
        toast.success('Interests saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/summary?guestId=${currentGuestId}`);
        return;
      }

      // Authenticated flow - save to API (already handled above)
      await saveInterestsToAPI();
      
      toast.success('Interests saved');
      clearDirtyState(); // Clear dirty state after successful save
      router.push(`/builder/summary?id=${resumeId}`);
    } catch (error: any) {
      console.error('Failed to save interests:', error);
      toast.error(error?.message || 'Failed to save interests');
    } finally {
      setSaving(false);
    }
  };

  const steps = [
    { id: 1, name: 'Personal Info', href: '/builder/personal', current: false },
    { id: 2, name: 'Experience', href: '/builder/experience', current: false },
    { id: 3, name: 'Projects', href: '/builder/projects', current: false },
    { id: 4, name: 'Education', href: '/builder/education', current: false },
    { id: 5, name: 'Certifications', href: '/builder/certifications', current: false },
    { id: 6, name: 'Skills', href: '/builder/skills', current: false },
    { id: 7, name: 'Languages', href: '/builder/languages', current: false },
    { id: 8, name: 'Interests', href: '/builder/interests', current: true },
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
                  Step {steps[7].id} of {steps.length} (Optional)
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
                    {steps.map((step, index) => (
                      <Link
                        key={step.id}
                        href={
                          resumeId 
                            ? `${step.href}?id=${resumeId}` 
                            : guestId 
                            ? `${step.href}?guestId=${guestId}` 
                            : step.href
                        }
                        className={`flex items-center gap-2 p-2 rounded-md transition-colors ${
                          step.current
                            ? 'bg-primary/10 text-primary font-semibold'
                            : 'text-muted-foreground hover:bg-accent'
                        }`}
                      >
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold ${
                          step.current
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-primary/10 text-primary'
                        }`}>
                          {step.id}
                        </div>
                        <span className="text-sm">{step.name}</span>
                      </Link>
                    ))}
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
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Interests</CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">Optional - Add your hobbies and interests</p>
                      </div>
                      <Button type="button" onClick={addInterest} variant="outline" size="sm">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Interest
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="ml-3 text-muted-foreground">Loading interests...</span>
                      </div>
                    ) : interests.length === 0 ? (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground mb-4">No interests added yet</p>
                        <p className="text-sm text-muted-foreground mb-4">This step is optional - you can skip it</p>
                        <Button type="button" onClick={addInterest} variant="outline">
                          <Plus className="mr-2 h-4 w-4" />
                          Add Your First Interest
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <AnimatePresence>
                          {interests.map((interest, index) => (
                            <motion.div
                              key={interest.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -20 }}
                            >
                              <Card>
                                <CardHeader>
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Interest #{index + 1}</CardTitle>
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => removeInterest(interest.id)}
                                    >
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-2">
                                    <Label>
                                      Interest Name
                                    </Label>
                                    <Input
                                      placeholder="Photography, Reading, Travel..."
                                      value={interest.name}
                                      onChange={(e) =>
                                        updateInterest(interest.id, 'name', e.target.value)
                                      }
                                    />
                                  </div>
                                </CardContent>
                              </Card>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                      </div>
                    )}

                    <div className="flex justify-between pt-4">
                      <Button type="button" variant="outline" asChild>
                        <Link href={
                          resumeId 
                            ? `/builder/languages?id=${resumeId}` 
                            : guestId 
                            ? `/builder/languages?guestId=${guestId}` 
                            : '/builder/languages'
                        }>
                          <ArrowLeft className="mr-2 h-4 w-4" />
                          Back
                        </Link>
                      </Button>
                      <Button
                        onClick={handleNext}
                        disabled={saving || loading || (!resumeId && !guestId)}
                        className="bg-gradient-to-r from-primary to-secondary"
                      >
                        {saving || loading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            {loading ? 'Loading...' : 'Saving...'}
                          </>
                        ) : (
                          <>
                            Next: Summary
                            <ArrowRight className="ml-2 h-4 w-4" />
                          </>
                        )}
                      </Button>
                    </div>
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












