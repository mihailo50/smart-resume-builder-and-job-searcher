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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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

interface Language {
  id: string;
  name: string;
  level: string;
}

const LANGUAGE_LEVELS = [
  { value: 'A1', label: 'A1 - Beginner' },
  { value: 'A2', label: 'A2 - Elementary' },
  { value: 'B1', label: 'B1 - Intermediate' },
  { value: 'B2', label: 'B2 - Upper Intermediate' },
  { value: 'C1', label: 'C1 - Advanced' },
  { value: 'C2', label: 'C2 - Proficient' },
  { value: 'Native', label: 'Native' },
];

export default function LanguagesPage() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState(82); // Step 7 of 11
  const [initialLanguages, setInitialLanguages] = useState<Language[]>([]);
  
  // Track dirty state
  const { markDirty, markClean } = useManualDirtyGuard('languages');
  useBeforeUnloadGuard(!isAuthenticated()); // Only for guest users

  // Track changes to languages array
  useEffect(() => {
    if (initialLanguages.length === 0 && languages.length === 0) return;
    
    const isDirty = JSON.stringify(languages) !== JSON.stringify(initialLanguages);
    if (isDirty) {
      markDirty();
    } else {
      markClean();
    }
  }, [languages, initialLanguages, markDirty, markClean]);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    if (guestId || (!resumeId && !isAuthenticated())) {
      // Guest mode - load from localStorage
      loadGuestLanguages();
    } else if (resumeId && isAuthenticated()) {
      // Authenticated mode - load from API
      loadLanguages();
    }
  }, [resumeId, guestId]);

  const loadLanguages = async () => {
    if (!resumeId) return;
    
    try {
      setLoading(true);
      const data = await api.get(`/v1/resumes/${resumeId}/languages/`);
      const loadedLanguages = data.map((lang: any) => ({
        id: lang.id,
        name: lang.name || '',
        level: lang.level || '',
      }));
      setLanguages(loadedLanguages);
      setInitialLanguages(JSON.parse(JSON.stringify(loadedLanguages))); // Deep copy
    } catch (error: any) {
      console.error('Failed to load languages:', error);
      toast.error('Failed to load languages');
    } finally {
      setLoading(false);
    }
  };

  const loadGuestLanguages = () => {
    try {
      const guestData = loadGuestResume();
      if (guestData.languages && guestData.languages.length > 0) {
        const loadedLanguages = guestData.languages.map((lang: any) => ({
          id: lang.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
          name: lang.name || '',
          level: lang.level || '',
        }));
        setLanguages(loadedLanguages);
        setInitialLanguages(JSON.parse(JSON.stringify(loadedLanguages))); // Deep copy
      }
    } catch (error) {
      console.error('Failed to load guest languages:', error);
    }
  };

  const addLanguage = () => {
    setLanguages([
      ...languages,
      {
        id: Date.now().toString(),
        name: '',
        level: '',
      },
    ]);
  };

  const removeLanguage = (id: string) => {
    setLanguages(languages.filter((lang) => lang.id !== id));
  };

  const updateLanguage = (id: string, field: keyof Language, value: string) => {
    setLanguages(
      languages.map((lang) => (lang.id === id ? { ...lang, [field]: value } : lang))
    );
  };

  const saveLanguagesToAPI = async () => {
    if (!resumeId) return;
    
    // Get existing languages from backend
    const existingLanguages = await api.get(`/v1/resumes/${resumeId}/languages/`);
    const existingIds = new Set(existingLanguages.map((lang: any) => lang.id));

    // Save/update each language
    for (const lang of languages) {
      if (!lang.name.trim()) continue; // Skip empty names
      
      const languageData: Record<string, any> = {
        name: lang.name.trim(),
        level: lang.level || '',
        order: languages.indexOf(lang),
      };
      
      // Filter out empty strings
      const filteredData = Object.fromEntries(
        Object.entries(languageData).filter(([_, v]) => v !== '' && v !== undefined)
      );
      
      if (lang.id && existingIds.has(lang.id)) {
        // Update existing
        await api.put(`/v1/resumes/${resumeId}/languages/${lang.id}/`, filteredData);
      } else {
        // Create new
        await api.post(`/v1/resumes/${resumeId}/languages/`, filteredData);
      }
    }

    // Delete removed languages
    for (const existing of existingLanguages) {
      if (!languages.some((lang) => lang.id === existing.id)) {
        await api.delete(`/v1/resumes/${resumeId}/languages/${existing.id}/`);
      }
    }
  };

  const handleNext = async () => {
    try {
      setSaving(true);

      if (guestId || (!resumeId && !isAuthenticated())) {
        // Guest flow - save to localStorage
        saveGuestResume({
          languages: languages
            .filter((lang) => lang.name.trim()) // Only save non-empty
            .map((lang, index) => ({
              id: lang.id,
              name: lang.name.trim(),
              level: lang.level || '',
              order: index,
            })),
        });
        
        const currentGuestId = getGuestResumeId();
        toast.success('Languages saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/interests?guestId=${currentGuestId}`);
        return;
      }

      // Authenticated flow - save to API (already handled above)
      await saveLanguagesToAPI();
      
      toast.success('Languages saved');
      clearDirtyState(); // Clear dirty state after successful save
      router.push(`/builder/interests?id=${resumeId}`);
    } catch (error: any) {
      console.error('Failed to save languages:', error);
      toast.error(error?.message || 'Failed to save languages');
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
    { id: 7, name: 'Languages', href: '/builder/languages', current: true },
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
                  Step {steps[6].id} of {steps.length}
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
                      <CardTitle>Languages</CardTitle>
                      <Button type="button" onClick={addLanguage} variant="outline" size="sm">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Language
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="ml-3 text-muted-foreground">Loading languages...</span>
                      </div>
                    ) : languages.length === 0 ? (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground mb-4">No languages added yet</p>
                        <Button type="button" onClick={addLanguage} variant="outline">
                          <Plus className="mr-2 h-4 w-4" />
                          Add Your First Language
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <AnimatePresence>
                          {languages.map((language, index) => (
                            <motion.div
                              key={language.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -20 }}
                            >
                              <Card>
                                <CardHeader>
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Language #{index + 1}</CardTitle>
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => removeLanguage(language.id)}
                                    >
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                      <Label>
                                        Language Name <span className="text-destructive">*</span>
                                      </Label>
                                      <Input
                                        placeholder="English"
                                        value={language.name}
                                        onChange={(e) =>
                                          updateLanguage(language.id, 'name', e.target.value)
                                        }
                                        required
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Proficiency Level</Label>
                                      <Select
                                        value={language.level}
                                        onValueChange={(value) =>
                                          updateLanguage(language.id, 'level', value)
                                        }
                                      >
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select level" />
                                        </SelectTrigger>
                                        <SelectContent>
                                          {LANGUAGE_LEVELS.map((level) => (
                                            <SelectItem key={level.value} value={level.value}>
                                              {level.label}
                                            </SelectItem>
                                          ))}
                                        </SelectContent>
                                      </Select>
                                    </div>
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
                            ? `/builder/skills?id=${resumeId}` 
                            : guestId 
                            ? `/builder/skills?guestId=${guestId}` 
                            : '/builder/skills'
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
                            Next: Interests
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











