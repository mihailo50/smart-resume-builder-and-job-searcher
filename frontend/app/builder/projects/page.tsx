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

interface Project {
  id: string;
  title: string;
  technologies: string;
  startDate: string;
  endDate: string;
  description: string;
}

export default function ProjectsPage() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState(33); // Step 3 of 9
  const [initialProjects, setInitialProjects] = useState<Project[]>([]);
  
  // Track dirty state
  const { markDirty, markClean } = useManualDirtyGuard('projects');
  useBeforeUnloadGuard(!isAuthenticated()); // Only for guest users

  // Track changes to projects array
  useEffect(() => {
    if (initialProjects.length === 0 && projects.length === 0) return;
    
    const isDirty = JSON.stringify(projects) !== JSON.stringify(initialProjects);
    if (isDirty) {
      markDirty();
    } else {
      markClean();
    }
  }, [projects, initialProjects, markDirty, markClean]);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    if (guestId || (!resumeId && !isAuthenticated())) {
      // Guest mode - load from localStorage
      loadGuestProjects();
    } else if (resumeId && isAuthenticated()) {
      // Authenticated mode - load from API
      loadProjects();
    }
  }, [resumeId, guestId]);

  const loadProjects = async () => {
    if (!resumeId) return;
    
    try {
      setLoading(true);
      const data = await api.get(`/v1/resumes/${resumeId}/projects/`);
      const loadedProjects = data.map((proj: any) => ({
        id: proj.id,
        title: proj.title || '',
        technologies: proj.technologies || '',
        startDate: proj.start_date ? new Date(proj.start_date).toISOString().slice(0, 7) : '',
        endDate: proj.end_date ? new Date(proj.end_date).toISOString().slice(0, 7) : '',
        description: proj.description || '',
      }));
      setProjects(loadedProjects);
      setInitialProjects(JSON.parse(JSON.stringify(loadedProjects))); // Deep copy
    } catch (error: any) {
      console.error('Failed to load projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const loadGuestProjects = () => {
    try {
      const guestData = loadGuestResume();
      if (guestData.projects && guestData.projects.length > 0) {
        const loadedProjects = guestData.projects.map((proj: any) => ({
          id: proj.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
          title: proj.title || '',
          technologies: proj.technologies || '',
          startDate: proj.startDate || '',
          endDate: proj.endDate || '',
          description: proj.description || '',
        }));
        setProjects(loadedProjects);
        setInitialProjects(JSON.parse(JSON.stringify(loadedProjects))); // Deep copy
      }
    } catch (error) {
      console.error('Failed to load guest projects:', error);
    }
  };

  const addProject = () => {
    setProjects([
      ...projects,
      {
        id: Date.now().toString(),
        title: '',
        technologies: '',
        startDate: '',
        endDate: '',
        description: '',
      },
    ]);
  };

  const removeProject = (id: string) => {
    setProjects(projects.filter((proj) => proj.id !== id));
  };

  const updateProject = (id: string, field: keyof Project, value: string) => {
    setProjects(
      projects.map((proj) => (proj.id === id ? { ...proj, [field]: value } : proj))
    );
  };

  const saveProjectsToAPI = async () => {
    if (!resumeId) return;
    
    // Get existing projects from backend
    const existingProjects = await api.get(`/v1/resumes/${resumeId}/projects/`);
    const existingIds = new Set(existingProjects.map((proj: any) => proj.id));

    // Save/update each project
    for (const proj of projects) {
      const projectData = {
        title: proj.title,
        technologies: proj.technologies || '',
        start_date: proj.startDate ? `${proj.startDate}-01` : undefined,
        end_date: proj.endDate ? `${proj.endDate}-01` : null,
        description: proj.description || '',
        order: projects.indexOf(proj),
      };
      
      // Filter out empty strings
      const filteredData = Object.fromEntries(
        Object.entries(projectData).filter(([_, v]) => v !== '' && v !== undefined)
      );
      
      if (proj.id && existingIds.has(proj.id)) {
        // Update existing
        await api.put(`/v1/resumes/${resumeId}/projects/${proj.id}/`, filteredData);
      } else {
        // Create new
        await api.post(`/v1/resumes/${resumeId}/projects/`, filteredData);
      }
    }

    // Delete removed projects
    for (const existing of existingProjects) {
      if (!projects.some((proj) => proj.id === existing.id)) {
        await api.delete(`/v1/resumes/${resumeId}/projects/${existing.id}/`);
      }
    }
  };

  const handleNext = async () => {
    try {
      setSaving(true);

      if (guestId || (!resumeId && !isAuthenticated())) {
        // Guest flow - save to localStorage
        saveGuestResume({
          projects: projects.map((proj, index) => ({
            id: proj.id,
            title: proj.title,
            technologies: proj.technologies,
            startDate: proj.startDate,
            endDate: proj.endDate,
            description: proj.description,
            order: index,
          })),
        });
        
        const currentGuestId = getGuestResumeId();
        toast.success('Projects saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/education?guestId=${currentGuestId}`);
        return;
      }

      // Authenticated flow - save to API (already handled above)
      await saveProjectsToAPI();
      
      toast.success('Projects saved');
      clearDirtyState(); // Clear dirty state after successful save
      router.push(`/builder/education?id=${resumeId}`);
    } catch (error: any) {
      console.error('Failed to save projects:', error);
      toast.error(error?.message || 'Failed to save projects');
    } finally {
      setSaving(false);
    }
  };

  const steps = [
    { id: 1, name: 'Personal Info', href: '/builder/personal', current: false },
    { id: 2, name: 'Experience', href: '/builder/experience', current: false },
    { id: 3, name: 'Projects', href: '/builder/projects', current: true },
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
                  Step {steps[2].id} of {steps.length}
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
                      <CardTitle>Projects</CardTitle>
                      <Button type="button" onClick={addProject} variant="outline" size="sm">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Project
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="ml-3 text-muted-foreground">Loading projects...</span>
                      </div>
                    ) : projects.length === 0 ? (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground mb-4">No projects added yet</p>
                        <Button type="button" onClick={addProject} variant="outline">
                          <Plus className="mr-2 h-4 w-4" />
                          Add Your First Project
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        <AnimatePresence>
                          {projects.map((project, index) => (
                            <motion.div
                              key={project.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -20 }}
                            >
                              <Card>
                                <CardHeader>
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Project #{index + 1}</CardTitle>
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => removeProject(project.id)}
                                    >
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2 md:col-span-2">
                                      <Label>
                                        Project Title <span className="text-destructive">*</span>
                                      </Label>
                                      <Input
                                        placeholder="E-commerce Platform"
                                        value={project.title}
                                        onChange={(e) =>
                                          updateProject(project.id, 'title', e.target.value)
                                        }
                                        required
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Technologies</Label>
                                      <Input
                                        placeholder="React, Node.js, PostgreSQL"
                                        value={project.technologies}
                                        onChange={(e) =>
                                          updateProject(project.id, 'technologies', e.target.value)
                                        }
                                      />
                                      <p className="text-xs text-muted-foreground">
                                        Comma-separated list of technologies used
                                      </p>
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Start Date</Label>
                                      <Input
                                        type="month"
                                        value={project.startDate}
                                        onChange={(e) =>
                                          updateProject(project.id, 'startDate', e.target.value)
                                        }
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>End Date</Label>
                                      <Input
                                        type="month"
                                        value={project.endDate}
                                        onChange={(e) =>
                                          updateProject(project.id, 'endDate', e.target.value)
                                        }
                                      />
                                    </div>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Description</Label>
                                    <Textarea
                                      placeholder="Describe the project, your role, and key achievements..."
                                      rows={4}
                                      value={project.description}
                                      onChange={(e) =>
                                        updateProject(project.id, 'description', e.target.value)
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
                            ? `/builder/experience?id=${resumeId}` 
                            : guestId 
                            ? `/builder/experience?guestId=${guestId}` 
                            : '/builder/experience'
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
                            Next: Education
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

