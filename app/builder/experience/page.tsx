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
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { ArrowRight, ArrowLeft, Plus, X, GripVertical, Loader2 } from 'lucide-react';
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
import { ResumeStepsSidebar } from '@/components/builder/steps-sidebar';

interface Experience {
  id: string;
  company: string;
  position: string;
  location: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
  description: string;
}

export default function ExperiencePage() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState(22); // Step 2 of 9
  const [initialExperiences, setInitialExperiences] = useState<Experience[]>([]);
  
  // Track dirty state
  const { markDirty, markClean } = useManualDirtyGuard('experience');
  useBeforeUnloadGuard(!isAuthenticated()); // Only for guest users

  // Track changes to experiences array
  useEffect(() => {
    if (initialExperiences.length === 0 && experiences.length === 0) return;
    
    const isDirty = JSON.stringify(experiences) !== JSON.stringify(initialExperiences);
    if (isDirty) {
      markDirty();
    } else {
      markClean();
    }
  }, [experiences, initialExperiences, markDirty, markClean]);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    if (guestId || (!resumeId && !isAuthenticated())) {
      // Guest mode - load from localStorage
      loadGuestExperiences();
    } else if (resumeId && isAuthenticated()) {
      // Authenticated mode - load from API
      loadExperiences();
    }
  }, [resumeId, guestId]);

  const loadExperiences = async () => {
    if (!resumeId) return;
    
    try {
      setLoading(true);
      const data = await api.get<any[]>(`/v1/resumes/${resumeId}/experiences/`);
      const loadedExperiences = data.map((exp: any) => ({
        id: exp.id,
        company: exp.company || '',
        position: exp.position || '',
        location: exp.location || '',
        startDate: exp.start_date ? new Date(exp.start_date).toISOString().slice(0, 7) : '',
        endDate: exp.end_date ? new Date(exp.end_date).toISOString().slice(0, 7) : '',
        isCurrent: exp.is_current || false,
        description: exp.description || '',
      }));
      setExperiences(loadedExperiences);
      setInitialExperiences(JSON.parse(JSON.stringify(loadedExperiences))); // Deep copy
    } catch (error: any) {
      console.error('Failed to load experiences:', error);
      toast.error('Failed to load experiences');
    } finally {
      setLoading(false);
    }
  };

  const loadGuestExperiences = () => {
    try {
      const guestData = loadGuestResume();
      if (guestData.experiences && guestData.experiences.length > 0) {
        const loadedExperiences = guestData.experiences.map((exp) => ({
          id: exp.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
          company: exp.company || '',
          position: exp.position || '',
          location: exp.location || '',
          startDate: exp.startDate || '',
          endDate: exp.endDate || '',
          isCurrent: exp.isCurrent || false,
          description: exp.description || '',
        }));
        setExperiences(loadedExperiences);
        setInitialExperiences(JSON.parse(JSON.stringify(loadedExperiences))); // Deep copy
      }
    } catch (error) {
      console.error('Failed to load guest experiences:', error);
    }
  };

  const addExperience = () => {
    setExperiences([
      ...experiences,
      {
        id: Date.now().toString(),
        company: '',
        position: '',
        location: '',
        startDate: '',
        endDate: '',
        isCurrent: false,
        description: '',
      },
    ]);
  };

  const removeExperience = (id: string) => {
    setExperiences(experiences.filter((exp) => exp.id !== id));
  };

  const updateExperience = (id: string, field: keyof Experience, value: string | boolean) => {
    setExperiences(
      experiences.map((exp) => (exp.id === id ? { ...exp, [field]: value } : exp))
    );
  };

  const saveExperiencesToAPI = async () => {
    if (!resumeId) return;
    
    // Get existing experiences from backend
    const existingExperiences = await api.get(`/v1/resumes/${resumeId}/experiences/`);
    const existingIds = new Set(existingExperiences.map((exp: any) => exp.id));

    // Save/update each experience
    for (const exp of experiences) {
      const experienceData = {
        company: exp.company,
        position: exp.position,
        location: exp.location || '',
        start_date: exp.startDate ? `${exp.startDate}-01` : undefined,
        end_date: exp.isCurrent ? null : exp.endDate ? `${exp.endDate}-01` : null,
        is_current: exp.isCurrent,
        description: exp.description || '',
      };

      if (existingIds.has(exp.id)) {
        // Update existing
        await api.put(`/v1/resumes/${resumeId}/experiences/${exp.id}/`, experienceData);
      } else {
        // Create new
        await api.post(`/v1/resumes/${resumeId}/experiences/`, experienceData);
      }
    }

    // Delete removed experiences
    const currentIds = new Set(experiences.map((exp) => exp.id));
    for (const existingExp of existingExperiences) {
      if (!currentIds.has(existingExp.id)) {
        await api.delete(`/v1/resumes/${resumeId}/experiences/${existingExp.id}/`);
      }
    }

    // Reorder experiences if order changed
    const experienceIds = experiences.map((exp) => exp.id);
    if (experienceIds.length > 1) {
      try {
        await api.patch(`/v1/resumes/${resumeId}/experiences/reorder/`, {
          item_ids: experienceIds,
        });
      } catch (error) {
        // Reordering is optional, don't fail if it errors
        console.warn('Failed to reorder experiences:', error);
      }
    }
  };

  const handleNext = async () => {
    try {
      setSaving(true);
      
      // Check if user is authenticated
      if (isAuthenticated() && resumeId) {
        // Authenticated flow - save to API
        await saveExperiencesToAPI();
      } else {
        // Guest flow - save to localStorage
        saveGuestResume({
          experiences: experiences.map((exp, index) => ({
            id: exp.id,
            company: exp.company,
            position: exp.position,
            location: exp.location || '',
            startDate: exp.startDate || '',
            endDate: exp.endDate || '',
            isCurrent: exp.isCurrent || false,
            description: exp.description || '',
            order: index,
          })),
        });
        
        const currentGuestId = getGuestResumeId();
        toast.success('Experience saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/projects?guestId=${currentGuestId}`);
        return;
      }

      // Authenticated flow - save to API (already handled above)
      await saveExperiencesToAPI();
      
      toast.success('Experiences saved');
      clearDirtyState(); // Clear dirty state after successful save
      router.push(`/builder/projects?id=${resumeId}`);
    } catch (error: any) {
      console.error('Failed to save experiences:', error);
      toast.error(error?.message || 'Failed to save experiences');
    } finally {
      setSaving(false);
    }
  };

  const steps = [
    { id: 1, name: 'Personal Info', href: '/builder/personal', current: false },
    { id: 2, name: 'Experience', href: '/builder/experience', current: true },
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
                  Step {steps[1].id} of {steps.length}
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
                <ResumeStepsSidebar currentStepId={2} resumeId={resumeId} guestId={guestId} />
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
                      <CardTitle>Work Experience</CardTitle>
                      <Button type="button" onClick={addExperience} variant="outline" size="sm">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Experience
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="ml-3 text-muted-foreground">Loading experiences...</span>
                      </div>
                    ) : experiences.length === 0 ? (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground mb-4">No experiences added yet</p>
                        <Button type="button" onClick={addExperience} variant="outline">
                          <Plus className="mr-2 h-4 w-4" />
                          Add Your First Experience
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        <AnimatePresence>
                          {experiences.map((experience, index) => (
                            <motion.div
                              key={experience.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -20 }}
                            >
                              <Card>
                                <CardHeader>
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Experience #{index + 1}</CardTitle>
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => removeExperience(experience.id)}
                                    >
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                      <Label>
                                        Position <span className="text-destructive">*</span>
                                      </Label>
                                      <Input
                                        placeholder="Software Engineer"
                                        value={experience.position}
                                        onChange={(e) =>
                                          updateExperience(experience.id, 'position', e.target.value)
                                        }
                                        required
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>
                                        Company <span className="text-destructive">*</span>
                                      </Label>
                                      <Input
                                        placeholder="Tech Corp"
                                        value={experience.company}
                                        onChange={(e) =>
                                          updateExperience(experience.id, 'company', e.target.value)
                                        }
                                        required
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Location</Label>
                                      <Input
                                        placeholder="New York, NY"
                                        value={experience.location}
                                        onChange={(e) =>
                                          updateExperience(experience.id, 'location', e.target.value)
                                        }
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Start Date</Label>
                                      <Input
                                        type="month"
                                        value={experience.startDate}
                                        onChange={(e) =>
                                          updateExperience(experience.id, 'startDate', e.target.value)
                                        }
                                      />
                                    </div>
                                    {!experience.isCurrent && (
                                      <div className="space-y-2">
                                        <Label>End Date</Label>
                                        <Input
                                          type="month"
                                          value={experience.endDate}
                                          onChange={(e) =>
                                            updateExperience(experience.id, 'endDate', e.target.value)
                                          }
                                        />
                                      </div>
                                    )}
                                    <div className="flex items-center space-x-2">
                                      <Checkbox
                                        id={`current-${experience.id}`}
                                        checked={experience.isCurrent}
                                        onCheckedChange={(checked) =>
                                          updateExperience(experience.id, 'isCurrent', !!checked)
                                        }
                                      />
                                      <Label
                                        htmlFor={`current-${experience.id}`}
                                        className="cursor-pointer"
                                      >
                                        I currently work here
                                      </Label>
                                    </div>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Description</Label>
                                    <Textarea
                                      placeholder="Describe your responsibilities and achievements..."
                                      rows={4}
                                      value={experience.description}
                                      onChange={(e) =>
                                        updateExperience(experience.id, 'description', e.target.value)
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
                            ? `/builder/personal?id=${resumeId}` 
                            : guestId 
                            ? `/builder/personal?guestId=${guestId}` 
                            : '/builder/personal'
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
                            Next: Projects
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
