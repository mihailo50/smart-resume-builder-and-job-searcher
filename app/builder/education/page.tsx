'use client';

import { useState, useEffect, Suspense } from 'react';
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
import { clearDirtyState } from '@/lib/use-dirty-guard';
import { ResumeStepsSidebar } from '@/components/builder/steps-sidebar';

interface Education {
  id: string;
  institution: string;
  degree: string;
  field: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
  description: string;
}

function EducationContent() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [educations, setEducations] = useState<Education[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState(36); // Step 4 of 11

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    if (guestId || (!resumeId && !isAuthenticated())) {
      // Guest mode - load from localStorage
      loadGuestEducations();
    } else if (resumeId && isAuthenticated()) {
      // Authenticated mode - load from API
      loadEducations();
    }
  }, [resumeId, guestId]);

  const loadEducations = async () => {
    if (!resumeId) return;
    
    try {
      setLoading(true);
      const data = await api.get<any[]>(`/v1/resumes/${resumeId}/educations/`);
      setEducations(
        data.map((edu: any) => ({
          id: edu.id,
          institution: edu.institution || '',
          degree: edu.degree || '',
          field: edu.field_of_study || '',
          startDate: edu.start_date ? new Date(edu.start_date).toISOString().slice(0, 7) : '',
          endDate: edu.end_date ? new Date(edu.end_date).toISOString().slice(0, 7) : '',
          isCurrent: edu.is_current || false,
          description: edu.description || '',
        }))
      );
    } catch (error: any) {
      console.error('Failed to load educations:', error);
      toast.error('Failed to load education entries');
    } finally {
      setLoading(false);
    }
  };

  const loadGuestEducations = () => {
    try {
      const guestData = loadGuestResume();
      if (guestData.educations && guestData.educations.length > 0) {
        setEducations(
          guestData.educations.map((edu) => ({
            id: edu.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
            institution: edu.institution || '',
            degree: edu.degree || '',
            field: edu.fieldOfStudy || '',
            startDate: edu.startDate || '',
            endDate: edu.endDate || '',
            isCurrent: edu.isCurrent || false,
            description: edu.description || '',
          }))
        );
      }
    } catch (error) {
      console.error('Failed to load guest educations:', error);
    }
  };

  const addEducation = () => {
    setEducations([
      ...educations,
      {
        id: Date.now().toString(),
        institution: '',
        degree: '',
        field: '',
        startDate: '',
        endDate: '',
        isCurrent: false,
        description: '',
      },
    ]);
  };

  const removeEducation = (id: string) => {
    setEducations(educations.filter((edu) => edu.id !== id));
  };

  const updateEducation = (id: string, field: keyof Education, value: string | boolean) => {
    setEducations(
      educations.map((edu) => (edu.id === id ? { ...edu, [field]: value } : edu))
    );
  };

  const saveEducationsToAPI = async () => {
    if (!resumeId) return;
    
    // Get existing educations from backend
    const existingEducations = await api.get<any[]>(`/v1/resumes/${resumeId}/educations/`);
    const existingIds = new Set(existingEducations.map((edu: any) => edu.id));

    // Save/update each education
    for (const edu of educations) {
      const educationData = {
        institution: edu.institution,
        degree: edu.degree,
        field_of_study: edu.field || '',
        start_date: edu.startDate ? `${edu.startDate}-01` : undefined,
        end_date: edu.isCurrent ? null : edu.endDate ? `${edu.endDate}-01` : null,
        is_current: edu.isCurrent,
        description: edu.description || '',
      };

      if (existingIds.has(edu.id)) {
        // Update existing
        await api.put(`/v1/resumes/${resumeId}/educations/${edu.id}/`, educationData);
      } else {
        // Create new
        await api.post(`/v1/resumes/${resumeId}/educations/`, educationData);
      }
    }

    // Delete removed educations
    const currentIds = new Set(educations.map((edu) => edu.id));
    for (const existingEdu of existingEducations) {
      if (!currentIds.has(existingEdu.id)) {
        await api.delete(`/v1/resumes/${resumeId}/educations/${existingEdu.id}/`);
      }
    }

    // Reorder educations if order changed
    const educationIds = educations.map((edu) => edu.id);
    if (educationIds.length > 1) {
      try {
        await api.patch(`/v1/resumes/${resumeId}/educations/reorder/`, {
          item_ids: educationIds,
        });
      } catch (error) {
        // Reordering is optional, don't fail if it errors
        console.warn('Failed to reorder educations:', error);
      }
    }
  };

  const handleNext = async () => {
    try {
      setSaving(true);
      
      // Check if user is authenticated
      if (isAuthenticated() && resumeId) {
        // Authenticated flow - save to API
        await saveEducationsToAPI();
        
        toast.success('Education entries saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/certifications?id=${resumeId}`);
      } else {
        // Guest flow - save to localStorage
        saveGuestResume({
          educations: educations.map((edu, index) => ({
            id: edu.id,
            institution: edu.institution,
            degree: edu.degree,
            fieldOfStudy: edu.field || '',
            startDate: edu.startDate || '',
            endDate: edu.endDate || '',
            isCurrent: edu.isCurrent || false,
            description: edu.description || '',
            order: index,
          })),
        });
        
        const currentGuestId = getGuestResumeId();
        toast.success('Education saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/certifications?guestId=${currentGuestId}`);
        return;
      }
    } catch (error: any) {
      console.error('Failed to save educations:', error);
      toast.error(error?.message || 'Failed to save education entries');
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">Step 4 of 11</span>
                <span className="text-sm font-medium text-muted-foreground">{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="lg:col-span-1"
              >
                <ResumeStepsSidebar currentStepId={4} resumeId={resumeId} guestId={guestId} />
              </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="lg:col-span-3"
            >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Education</CardTitle>
                  <Button type="button" onClick={addEducation} variant="outline" size="sm">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Education
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">

                    {loading ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="ml-3 text-muted-foreground">Loading education entries...</span>
                      </div>
                    ) : educations.length === 0 ? (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground mb-4">No education entries added yet</p>
                        <Button type="button" onClick={addEducation} variant="outline">
                          <Plus className="mr-2 h-4 w-4" />
                          Add Your First Education Entry
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        <AnimatePresence>
                          {educations.map((education, index) => (
                            <motion.div
                              key={education.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -20 }}
                            >
                              <Card>
                                <CardHeader>
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Education #{index + 1}</CardTitle>
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => removeEducation(education.id)}
                                    >
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                      <Label>
                                        Degree <span className="text-destructive">*</span>
                                      </Label>
                                      <Input
                                        placeholder="Bachelor of Science"
                                        value={education.degree}
                                        onChange={(e) =>
                                          updateEducation(education.id, 'degree', e.target.value)
                                        }
                                        required
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>
                                        Institution <span className="text-destructive">*</span>
                                      </Label>
                                      <Input
                                        placeholder="University Name"
                                        value={education.institution}
                                        onChange={(e) =>
                                          updateEducation(education.id, 'institution', e.target.value)
                                        }
                                        required
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Field of Study</Label>
                                      <Input
                                        placeholder="Computer Science"
                                        value={education.field}
                                        onChange={(e) =>
                                          updateEducation(education.id, 'field', e.target.value)
                                        }
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Start Date</Label>
                                      <Input
                                        type="month"
                                        value={education.startDate}
                                        onChange={(e) =>
                                          updateEducation(education.id, 'startDate', e.target.value)
                                        }
                                      />
                                    </div>
                                    {!education.isCurrent && (
                                      <div className="space-y-2">
                                        <Label>End Date</Label>
                                        <Input
                                          type="month"
                                          value={education.endDate}
                                          onChange={(e) =>
                                            updateEducation(education.id, 'endDate', e.target.value)
                                          }
                                        />
                                      </div>
                                    )}
                                    <div className="flex items-center space-x-2">
                                      <Checkbox
                                        id={`current-${education.id}`}
                                        checked={education.isCurrent}
                                        onCheckedChange={(checked) =>
                                          updateEducation(education.id, 'isCurrent', !!checked)
                                        }
                                      />
                                      <Label htmlFor={`current-${education.id}`} className="cursor-pointer">
                                        Currently studying
                                      </Label>
                                    </div>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Description</Label>
                                    <Textarea
                                      placeholder="Additional details or achievements..."
                                      rows={3}
                                      value={education.description}
                                      onChange={(e) =>
                                        updateEducation(education.id, 'description', e.target.value)
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
                            ? `/builder/projects?id=${resumeId}` 
                            : guestId 
                            ? `/builder/projects?guestId=${guestId}` 
                            : '/builder/projects'
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
                            Next: Certifications
                            <ArrowRight className="ml-2 h-4 w-4" />
                          </>
                      )}
                    </Button>
                  </div>
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

export default function EducationPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <EducationContent />
    </Suspense>
  );
}
