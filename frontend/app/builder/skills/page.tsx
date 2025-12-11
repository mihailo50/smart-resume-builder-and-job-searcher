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
import { Badge } from '@/components/ui/badge';
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
import { ResumeStepsSidebar } from '@/components/builder/steps-sidebar';

interface Skill {
  id: string;
  name: string;
  category: string;
  level: string;
}

export default function SkillsPage() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState(55); // Step 6 of 11

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    if (guestId || (!resumeId && !isAuthenticated())) {
      // Guest mode - load from localStorage
      loadGuestSkills();
    } else if (resumeId && isAuthenticated()) {
      // Authenticated mode - load from API
      loadSkills();
    }
  }, [resumeId, guestId]);

  const loadSkills = async () => {
    if (!resumeId) return;
    
    try {
      setLoading(true);
      const data = await api.get<any[]>(`/v1/resumes/${resumeId}/skills/`);
      setSkills(
        data.map((skill: any) => ({
          id: skill.id,
          name: skill.name || '',
          category: skill.category || 'Programming',
          level: skill.level || 'intermediate',
        }))
      );
    } catch (error: any) {
      console.error('Failed to load skills:', error);
      toast.error('Failed to load skills');
    } finally {
      setLoading(false);
    }
  };

  const loadGuestSkills = () => {
    try {
      const guestData = loadGuestResume();
      if (guestData.skills && guestData.skills.length > 0) {
        setSkills(
          guestData.skills.map((skill) => ({
            id: skill.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
            name: skill.name || '',
            category: skill.category || 'Programming',
            level: skill.level || 'intermediate',
          }))
        );
      }
    } catch (error) {
      console.error('Failed to load guest skills:', error);
    }
  };

  const addSkill = () => {
    setSkills([
      ...skills,
      { id: Date.now().toString(), name: '', category: 'Programming', level: 'intermediate' },
    ]);
  };

  const removeSkill = (id: string) => {
    setSkills(skills.filter((skill) => skill.id !== id));
  };

  const updateSkill = (id: string, field: keyof Skill, value: string) => {
    setSkills(skills.map((skill) => (skill.id === id ? { ...skill, [field]: value } : skill)));
  };

  const saveSkillsToAPI = async () => {
    if (!resumeId) return;
    
    // Get existing skills from backend
    const existingSkills = await api.get(`/v1/resumes/${resumeId}/skills/`);
    const existingIds = new Set(existingSkills.map((skill: any) => skill.id));

    // Save/update each skill
    for (const skill of skills) {
      if (!skill.name.trim()) continue; // Skip empty skills

      const skillData = {
        name: skill.name,
        category: skill.category || '',
        level: skill.level || 'intermediate',
      };

      if (existingIds.has(skill.id)) {
        // Update existing
        await api.put(`/v1/resumes/${resumeId}/skills/${skill.id}/`, skillData);
      } else {
        // Create new
        await api.post(`/v1/resumes/${resumeId}/skills/`, skillData);
      }
    }

    // Delete removed skills
    const currentIds = new Set(skills.filter(s => s.name.trim()).map((skill) => skill.id));
    for (const existingSkill of existingSkills) {
      if (!currentIds.has(existingSkill.id)) {
        await api.delete(`/v1/resumes/${resumeId}/skills/${existingSkill.id}/`);
      }
    }
  };

  const handleNext = async () => {
    try {
      setSaving(true);
      
      // Check if user is authenticated
      if (isAuthenticated() && resumeId) {
        // Authenticated flow - save to API
        await saveSkillsToAPI();
        
        toast.success('Skills saved');
        router.push(`/builder/languages?id=${resumeId}`);
      } else {
        // Guest flow - save to localStorage
        saveGuestResume({
          skills: skills
            .filter(s => s.name.trim()) // Only save non-empty skills
            .map((skill, index) => ({
              id: skill.id,
              name: skill.name,
              category: skill.category || 'Programming',
              level: skill.level || 'intermediate',
              order: index,
            })),
        });
        
        const currentGuestId = getGuestResumeId();
        toast.success('Skills saved');
        router.push(`/builder/languages?guestId=${currentGuestId}`);
        return;
      }
    } catch (error: any) {
      console.error('Failed to save skills:', error);
      toast.error(error?.message || 'Failed to save skills');
    } finally {
      setSaving(false);
    }
  };

  const categories = ['Programming', 'Tools', 'Languages', 'Soft Skills', 'Other'];
  const levels = [
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' },
    { value: 'expert', label: 'Expert' },
  ];

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-6xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">Step 6 of 11</span>
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
                <ResumeStepsSidebar currentStepId={6} resumeId={resumeId} guestId={guestId} />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="lg:col-span-3"
              >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Skills</CardTitle>
                  <Button type="button" onClick={addSkill} variant="outline" size="sm">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Skill
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      <span className="ml-3 text-muted-foreground">Loading skills...</span>
                    </div>
                  ) : skills.length === 0 ? (
                    <div className="text-center py-12">
                      <p className="text-muted-foreground mb-4">No skills added yet</p>
                      <Button type="button" onClick={addSkill} variant="outline">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Your First Skill
                      </Button>
                    </div>
                  ) : (
                    <AnimatePresence>
                      {skills.map((skill, index) => (
                        <motion.div
                          key={skill.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3 }}
                          className="mb-4"
                        >
                          <Card>
                            <CardContent className="p-4">
                              <div className="flex items-center gap-4">
                                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                                  <div className="space-y-2">
                                    <Label>Skill Name</Label>
                                    <Input
                                      placeholder="JavaScript"
                                      value={skill.name}
                                      onChange={(e) => updateSkill(skill.id, 'name', e.target.value)}
                                    />
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Category</Label>
                                    <Select
                                      value={skill.category}
                                      onValueChange={(value) => updateSkill(skill.id, 'category', value)}
                                    >
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {categories.map((cat) => (
                                          <SelectItem key={cat} value={cat}>
                                            {cat}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Level</Label>
                                    <Select
                                      value={skill.level}
                                      onValueChange={(value) => updateSkill(skill.id, 'level', value)}
                                    >
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {levels.map((level) => (
                                          <SelectItem key={level.value} value={level.value}>
                                            {level.label}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>
                                </div>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => removeSkill(skill.id)}
                                  className="flex-shrink-0"
                                >
                                  <X className="h-4 w-4" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  )}

                  <div className="flex justify-between pt-4">
                    <Button type="button" variant="outline" asChild>
                        <Link href={
                          resumeId 
                            ? `/builder/certifications?id=${resumeId}` 
                            : guestId 
                            ? `/builder/certifications?guestId=${guestId}` 
                            : '/builder/certifications'
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
                            Next: Languages
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


