'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Sparkles, Loader2, Mail, Github, CheckCircle2, LogIn } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { guestResumeToApiFormat, clearGuestResume, getGuestResumeId, hasGuestResumeData } from '@/lib/guest-resume';
import { FinalizingLoader } from '@/components/resume/finalizing-loader';

const hasValue = (value: unknown) => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') {
    return value.trim().length > 0;
  }
  return true;
};

const filterEmptyFields = <T extends Record<string, any>>(payload: T) => {
  // Filter out null, undefined, and empty strings
  return Object.fromEntries(
    Object.entries(payload).filter(([_, v]) => v != null && v !== '')
  ) as Partial<T>;
};

interface SignupModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSignupSuccess?: (resumeId: string) => Promise<void> | void;
  guestResumeId?: string;
  prefillEmail?: string;
}

interface RegisterResponse {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name?: string;
  };
}

interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
  token_type: string;
  user: {
    id: string;
    email: string;
    user_metadata?: any;
  };
}

// Login form schema
const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function SignupModal({ open, onOpenChange, onSignupSuccess, guestResumeId, prefillEmail }: SignupModalProps) {
  const router = useRouter();
  // Check if guest has data to show appropriate message
  const hasGuestData = hasGuestResumeData();
  // Default to login tab if guest has data (existing users should log in)
  const [activeTab, setActiveTab] = useState<'signup' | 'login'>(hasGuestData ? 'login' : 'signup');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [signingUp, setSigningUp] = useState(false);
  const [loggingIn, setLoggingIn] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [finalizingProgress, setFinalizingProgress] = useState(0);
  const [finalizingStep, setFinalizingStep] = useState('');
  const [finalizingComplete, setFinalizingComplete] = useState(false);

  // Login form
  const {
    register: registerLogin,
    handleSubmit: handleLoginSubmit,
    formState: { errors: loginErrors },
    setValue: setLoginValue,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    if (open && prefillEmail) {
      setEmail(prefillEmail);
      setLoginValue('email', prefillEmail);
    }
    // Reset to appropriate tab when modal opens
    if (open) {
      setActiveTab(hasGuestResumeData() ? 'login' : 'signup');
    }
  }, [open, prefillEmail, setLoginValue]);

  /**
   * Robust sequencer for saving guest resume data after signup.
   * Collects all save promises and awaits them together to prevent race conditions.
   * Includes rollback (resume deletion) on any failure.
   */
  const replayGuestResume = async (
    resumeId: string,
    guestData: ReturnType<typeof guestResumeToApiFormat>,
    options: {
      defaultFullName?: string;
      defaultEmail?: string;
      registeredFullName?: string;
    },
    onProgress?: (progress: number, step: string) => void
  ): Promise<void> => {
    const { defaultFullName, defaultEmail, registeredFullName } = options;
    
    // Collect all save promises
    const promises: Promise<any>[] = [];
    let totalSteps = 0;
    let completedSteps = 0;
    
    const updateProgress = (step: string) => {
      completedSteps++;
      const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
      onProgress?.(progress, step);
    };
    
    try {
      // Step 1: Save Personal Info
      if (guestData.personal) {
        const personalData: Record<string, any> = {};
        
        const fullName = guestData.personal.fullName || registeredFullName || defaultFullName;
        if (fullName && fullName.trim()) personalData.full_name = fullName.trim();
        
        const emailValue = guestData.personal.email || defaultEmail;
        if (emailValue && emailValue.trim()) personalData.email = emailValue.trim();
        
        if (guestData.personal.phone && guestData.personal.phone.trim()) {
          personalData.phone = guestData.personal.phone.trim();
        }
        if (guestData.personal.location && guestData.personal.location.trim()) {
          personalData.location = guestData.personal.location.trim();
        }
        if (guestData.personal.linkedin && guestData.personal.linkedin.trim()) {
          personalData.linkedin_url = guestData.personal.linkedin.trim();
        }
        if (guestData.personal.github && guestData.personal.github.trim()) {
          personalData.github_url = guestData.personal.github.trim();
        }
        if (guestData.personal.portfolio && guestData.personal.portfolio.trim()) {
          personalData.portfolio_url = guestData.personal.portfolio.trim();
        }
        
        const personalPayload = Object.fromEntries(
          Object.entries(personalData).filter(([_, v]) => v != null && v !== '' && (typeof v !== 'string' || v.trim() !== ''))
        );
        
        if (personalPayload.full_name || Object.keys(personalPayload).length > 0) {
          totalSteps++;
          promises.push(
            api.put(`/v1/resumes/${resumeId}/personal/`, personalPayload)
              .then(() => updateProgress('Personal information saved'))
              .catch((err) => {
                console.error('Failed to save personal info:', err);
                throw new Error('Failed to save personal information');
              })
          );
        }
      }
      
      // Step 2: Save Experiences
      if (guestData.experiences && guestData.experiences.length > 0) {
        const validExperiences = guestData.experiences.filter(
          (exp: any) => exp.company && exp.position && exp.company.trim() && exp.position.trim()
        );
        
        if (validExperiences.length > 0) {
          totalSteps++;
          const experiencePromises = validExperiences.map((exp: any) => {
            const experienceData: Record<string, any> = {
              company: exp.company,
              position: exp.position,
            };
            
            if (exp.location) experienceData.location = exp.location;
            if (exp.startDate) experienceData.start_date = exp.startDate;
            if (exp.endDate) experienceData.end_date = exp.endDate;
            if (exp.isCurrent !== undefined) experienceData.is_current = exp.isCurrent;
            if (exp.description) experienceData.description = exp.description;
            if (typeof exp.order === 'number') experienceData.order = exp.order;
            
            const experiencePayload = Object.fromEntries(
              Object.entries(experienceData).filter(([_, v]) => v != null && v !== '')
            );
            
            return api.post(`/v1/resumes/${resumeId}/experiences/`, experiencePayload);
          });
          
          promises.push(
            Promise.all(experiencePromises)
              .then(() => updateProgress(`Saved ${validExperiences.length} work experience${validExperiences.length > 1 ? 's' : ''}`))
              .catch((err) => {
                console.error('Failed to save experiences:', err);
                throw new Error('Failed to save work experiences');
              })
          );
        }
      }
      
      // Step 3: Save Projects
      if (guestData.projects && guestData.projects.length > 0) {
        const validProjects = guestData.projects.filter(
          (proj: any) => proj.title && proj.title.trim()
        );
        
        if (validProjects.length > 0) {
          totalSteps++;
          const projectPromises = validProjects.map((proj: any) => {
            const projectData: Record<string, any> = {
              title: proj.title,
            };
            
            if (proj.technologies) projectData.technologies = proj.technologies;
            if (proj.startDate) projectData.start_date = proj.startDate;
            if (proj.endDate) projectData.end_date = proj.endDate;
            if (proj.description) projectData.description = proj.description;
            if (typeof proj.order === 'number') projectData.order = proj.order;
            
            const projectPayload = Object.fromEntries(
              Object.entries(projectData).filter(([_, v]) => v != null && v !== '')
            );
            
            return api.post(`/v1/resumes/${resumeId}/projects/`, projectPayload);
          });
          
          promises.push(
            Promise.all(projectPromises)
              .then(() => updateProgress(`Saved ${validProjects.length} project${validProjects.length > 1 ? 's' : ''}`))
              .catch((err) => {
                console.error('Failed to save projects:', err);
                throw new Error('Failed to save projects');
              })
          );
        }
      }
      
      // Step 4: Save Certifications
      if (guestData.certifications && guestData.certifications.length > 0) {
        const validCertifications = guestData.certifications.filter(
          (cert: any) => cert.title && cert.title.trim()
        );
        
        if (validCertifications.length > 0) {
          totalSteps++;
          const certificationPromises = validCertifications.map((cert: any) => {
            const certificationData: Record<string, any> = {
              title: cert.title,
            };
            
            if (cert.issuer) certificationData.issuer = cert.issuer;
            if (cert.issueDate) certificationData.issue_date = cert.issueDate;
            if (cert.doesNotExpire) {
              certificationData.expiration_date = null;
            } else if (cert.expirationDate) {
              certificationData.expiration_date = cert.expirationDate;
            }
            if (cert.credentialId) certificationData.credential_id = cert.credentialId;
            if (cert.url) certificationData.url = cert.url;
            if (cert.description) certificationData.description = cert.description;
            if (typeof cert.order === 'number') certificationData.order = cert.order;
            
            const certificationPayload = Object.fromEntries(
              Object.entries(certificationData).filter(([_, v]) => v != null && v !== '')
            );
            
            return api.post(`/v1/resumes/${resumeId}/certifications/`, certificationPayload);
          });
          
          promises.push(
            Promise.all(certificationPromises)
              .then(() => updateProgress(`Saved ${validCertifications.length} certification${validCertifications.length > 1 ? 's' : ''}`))
              .catch((err) => {
                console.error('Failed to save certifications:', err);
                throw new Error('Failed to save certifications');
              })
          );
        }
      }
      
      // Step 5: Save Educations
      if (guestData.educations && guestData.educations.length > 0) {
        const validEducations = guestData.educations.filter(
          (edu: any) => edu.institution && edu.degree && edu.institution.trim() && edu.degree.trim()
        );
        
        if (validEducations.length > 0) {
          totalSteps++;
          const educationPromises = validEducations.map((edu: any) => {
            const educationData: Record<string, any> = {
              institution: edu.institution,
              degree: edu.degree,
            };
            
            if (edu.fieldOfStudy) educationData.field_of_study = edu.fieldOfStudy;
            if (edu.startDate) educationData.start_date = edu.startDate;
            if (edu.endDate) educationData.end_date = edu.endDate;
            if (edu.isCurrent !== undefined) educationData.is_current = edu.isCurrent;
            if (edu.description) educationData.description = edu.description;
            if (typeof edu.order === 'number') educationData.order = edu.order;
            
            const educationPayload = Object.fromEntries(
              Object.entries(educationData).filter(([_, v]) => v != null && v !== '')
            );
            
            return api.post(`/v1/resumes/${resumeId}/educations/`, educationPayload);
          });
          
          promises.push(
            Promise.all(educationPromises)
              .then(() => updateProgress(`Saved ${validEducations.length} education${validEducations.length > 1 ? 's' : ''}`))
              .catch((err) => {
                console.error('Failed to save educations:', err);
                throw new Error('Failed to save education entries');
              })
          );
        }
      }
      
      // Step 4: Save Skills
      if (guestData.skills && guestData.skills.length > 0) {
        const validSkills = guestData.skills.filter(
          (skill: any) => skill.name && skill.name.trim()
        );
        
        if (validSkills.length > 0) {
          totalSteps++;
          const skillPromises = validSkills.map((skill: any) => {
            const skillData: Record<string, any> = {
              name: skill.name,
            };
            
            if (skill.category) skillData.category = skill.category;
            if (skill.level) skillData.level = skill.level;
            if (typeof skill.order === 'number') skillData.order = skill.order;
            
            const skillPayload = Object.fromEntries(
              Object.entries(skillData).filter(([_, v]) => v != null && v !== '')
            );
            
            return api.post(`/v1/resumes/${resumeId}/skills/`, skillPayload);
          });
          
          promises.push(
            Promise.all(skillPromises)
              .then(() => updateProgress(`Saved ${validSkills.length} skill${validSkills.length > 1 ? 's' : ''}`))
              .catch((err) => {
                console.error('Failed to save skills:', err);
                throw new Error('Failed to save skills');
              })
          );
        }
      }
      
      // Step 5: Save Optimized Summary
      const optimizedSummaryText = guestData.optimizedSummary || '';
      if (optimizedSummaryText && optimizedSummaryText.trim()) {
        totalSteps++;
        promises.push(
          api.put(`/v1/resumes/${resumeId}/optimized-summary/`, {
            optimized_summary: optimizedSummaryText,
          })
            .then(() => updateProgress('AI-optimized summary saved'))
            .catch((err) => {
              console.error('Failed to save optimized summary:', err);
              throw new Error('Failed to save AI-optimized summary');
            })
        );
      }
      
      // Step 6: Save Short Summary/Tagline
      const shortSummary = (
        guestData.personal?.professionalTagline ||
        guestData.personal?.summary ||
        ''
      )
        .slice(0, 300)
        .trim();
      if (shortSummary) {
        totalSteps++;
        promises.push(
          api.put(`/v1/resumes/${resumeId}/summary/`, {
            professional_tagline: shortSummary,
            summary: shortSummary,
          })
            .then(() => updateProgress('Professional tagline saved'))
            .catch((err) => {
              console.error('Failed to save summary:', err);
              throw new Error('Failed to save professional tagline');
            })
        );
      }
      
      // Update progress to show we're starting
      if (promises.length > 0) {
        onProgress?.(0, `Finalizing ${promises.length} section${promises.length > 1 ? 's' : ''}...`);
      }
      
      // Await ALL promises together - this ensures everything completes before export
      await Promise.all(promises);
      
      // Mark as complete
      onProgress?.(100, 'All data saved successfully!');
    } catch (error: any) {
      console.error('Error in replayGuestResume:', error);
      throw error;
    }
  };

  /**
   * Handle login and convert guest data if present
   */
  const handleLogin = async (data: LoginFormData) => {
    try {
      setLoggingIn(true);
      
      // Login user
      const response = await api.post<LoginResponse>('/v1/auth/login/', {
        email: data.email,
        password: data.password,
      });

      // Store token in localStorage
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        localStorage.setItem('user', JSON.stringify(response.user));
        
        // Check if guest has data to convert
        if (hasGuestData && guestResumeId) {
          setFinalizing(true);
          setFinalizingProgress(0);
          setFinalizingStep('Creating resume...');
          setFinalizingComplete(false);
          
          let savedResumeId: string | null = null;
          
          try {
            // Step 1: Create resume
            const guestData = guestResumeToApiFormat();
            setFinalizingStep('Creating resume...');
            setFinalizingProgress(5);
            
            const savedResume = await api.post<{ id: string }>('/v1/resumes/', {
              title: guestData.title || 'My Resume',
              professional_tagline: guestData.professional_tagline || guestData.summary || '',
              summary: guestData.summary || '',
              optimized_summary: guestData.optimized_summary || '',
            });
            
            savedResumeId = savedResume.id;
            
            // Step 2: Collect all save promises and await them together
            setFinalizingStep('Preparing to save data...');
            setFinalizingProgress(10);
            
            await replayGuestResume(
              savedResume.id,
              guestData,
              {
                defaultFullName: response.user.user_metadata?.full_name || '',
                defaultEmail: data.email,
                registeredFullName: response.user.user_metadata?.full_name || '',
              },
              (progress, step) => {
                // Map progress from 10-90% (reserve 10% for completion)
                const mappedProgress = 10 + Math.round((progress / 100) * 80);
                setFinalizingProgress(mappedProgress);
                setFinalizingStep(step);
              }
            );
            
            // Step 3: Mark as complete
            setFinalizingComplete(true);
            setFinalizingProgress(100);
            setFinalizingStep('All data saved successfully!');
            
            // Small delay to show completion
            await new Promise(resolve => setTimeout(resolve, 500));
            
            clearGuestResume();
            
            toast.success('Resume saved to your account!');
            
            // Step 4: Only after ALL saves complete, trigger export
            if (onSignupSuccess && savedResumeId) {
              await onSignupSuccess(savedResumeId);
            }
            
            onOpenChange(false);
            // Redirect to preview/export
            router.push(`/builder/preview?resumeId=${savedResumeId}`);
          } catch (error: any) {
            console.error('Failed to save guest resume:', error);
            
            // Rollback: Delete the resume if it was created
            if (savedResumeId) {
              try {
                await api.delete(`/v1/resumes/${savedResumeId}/`);
                console.log('Rollback: Deleted incomplete resume');
              } catch (rollbackError) {
                console.error('Failed to rollback (delete resume):', rollbackError);
              }
            }
            
            toast.error(
              error?.message || 'Login successful, but failed to save resume. Please try again.',
              {
                description: 'You can create a new resume from the dashboard.',
                duration: 5000,
              }
            );
            
            setFinalizing(false);
            setFinalizingProgress(0);
            setFinalizingStep('');
            
            // Still close modal and redirect to dashboard on error
            onOpenChange(false);
            router.push('/dashboard');
          }
        } else {
          // No guest data, just login normally
          toast.success('Logged in successfully!');
          onOpenChange(false);
          router.push('/dashboard');
        }
      } else {
        toast.error('Login failed: No token received');
      }
    } catch (error: any) {
      console.error('Login failed:', error);
      
      let errorMessage = 'Login failed. Please check your credentials.';
      if (error.response) {
        const backendError = error.response;
        if (backendError.errors && typeof backendError.errors === 'object') {
          const errorValues = Object.values(backendError.errors);
          if (errorValues.length > 0) {
            const firstError = errorValues[0];
            errorMessage = Array.isArray(firstError) ? String(firstError[0]) : String(firstError);
          }
        } else if (backendError.message) {
          errorMessage = backendError.message;
        } else if (backendError.error) {
          errorMessage = backendError.error;
        }
      } else if (error.message && !error.message.includes('HTTP error!')) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setLoggingIn(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please enter email and password');
      return;
    }

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    try {
      setSigningUp(true);
      
      // Register user
      const response = await api.post<RegisterResponse>('/v1/auth/register/', {
        email,
        password,
        full_name: name || '',
      });

      // Store token in localStorage
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        localStorage.setItem('user', JSON.stringify(response.user));
        
        // Save guest resume to backend
        if (guestResumeId) {
          setFinalizing(true);
          setFinalizingProgress(0);
          setFinalizingStep('Creating resume...');
          setFinalizingComplete(false);
          
          let savedResumeId: string | null = null;
          
          try {
            // Step 1: Create resume
            const guestData = guestResumeToApiFormat();
            setFinalizingStep('Creating resume...');
            setFinalizingProgress(5);
            
            const savedResume = await api.post<{ id: string }>('/v1/resumes/', {
              title: guestData.title || 'My Resume',
              professional_tagline: guestData.professional_tagline || guestData.summary || '',
              summary: guestData.summary || '',
              optimized_summary: guestData.optimized_summary || '',
            });
            
            savedResumeId = savedResume.id;
            
            // Step 2: Collect all save promises and await them together
            setFinalizingStep('Preparing to save data...');
            setFinalizingProgress(10);
            
            await replayGuestResume(
              savedResume.id,
              guestData,
              {
                defaultFullName: name,
                defaultEmail: email,
                registeredFullName: response.user.full_name,
              },
              (progress, step) => {
                // Map progress from 10-90% (reserve 10% for completion)
                const mappedProgress = 10 + Math.round((progress / 100) * 80);
                setFinalizingProgress(mappedProgress);
                setFinalizingStep(step);
              }
            );
            
            // Step 3: Mark as complete
            setFinalizingComplete(true);
            setFinalizingProgress(100);
            setFinalizingStep('All data saved successfully!');
            
            // Small delay to show completion
            await new Promise(resolve => setTimeout(resolve, 500));
            
            clearGuestResume();
            
            toast.success('Resume saved to your account!');
            
            // Step 4: Only after ALL saves complete, trigger export
            if (onSignupSuccess && savedResumeId) {
              await onSignupSuccess(savedResumeId);
            }
            
            onOpenChange(false);
          } catch (error: any) {
            console.error('Failed to save guest resume:', error);
            
            // Rollback: Delete the resume if it was created
            if (savedResumeId) {
              try {
                await api.delete(`/v1/resumes/${savedResumeId}/`);
                console.log('Rollback: Deleted incomplete resume');
              } catch (rollbackError) {
                console.error('Failed to rollback (delete resume):', rollbackError);
              }
            }
            
            toast.error(
              error?.message || 'Account created, but failed to save resume. Please try again.',
              {
                description: 'Your account was created successfully. You can create a new resume from the dashboard.',
                duration: 5000,
              }
            );
            
            setFinalizing(false);
            setFinalizingProgress(0);
            setFinalizingStep('');
            
            // Don't close modal on error - let user see the error message
            // User can try again or continue to dashboard
          }
        } else {
          toast.success('Account created successfully!');
          onOpenChange(false);
          router.push('/dashboard');
        }
      } else {
        toast.error('Registration failed: No token received');
      }
    } catch (error: any) {
      console.error('Registration failed:', error);
      
      let errorMessage = 'Registration failed. Please try again.';
      if (error.response) {
        const backendError = error.response;
        if (backendError.errors && typeof backendError.errors === 'object') {
          const errorValues = Object.values(backendError.errors);
          if (errorValues.length > 0) {
            const firstError = errorValues[0];
            errorMessage = Array.isArray(firstError) ? String(firstError[0]) : String(firstError);
          }
        } else if (backendError.message) {
          errorMessage = backendError.message;
        } else if (backendError.error) {
          errorMessage = backendError.error;
        }
      } else if (error.message && !error.message.includes('HTTP error!')) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setSigningUp(false);
    }
  };

  return (
    <>
      {finalizing && (
        <FinalizingLoader
          progress={finalizingProgress}
          currentStep={finalizingStep}
          isComplete={finalizingComplete}
        />
      )}
      
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-center flex items-center justify-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            {hasGuestData ? 'Save Your Progress' : 'Create a Free Account'}
          </DialogTitle>
          <DialogDescription className="text-center pt-2">
            {hasGuestData 
              ? 'Already have an account? Log in to save your progress. Or create a new account to get started.'
              : 'Sign up to save your progress permanently and download your resume any time—it only takes 10 seconds.'}
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'signup' | 'login')} className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="signup">Sign Up</TabsTrigger>
            <TabsTrigger value="login">Log In</TabsTrigger>
          </TabsList>

          {/* Sign Up Tab */}
          <TabsContent value="signup" className="space-y-4 mt-4">
            <form onSubmit={handleRegister} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="modal-name">Full Name</Label>
            <Input
              id="modal-name"
              placeholder="John Doe"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={signingUp}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="modal-email">Email <span className="text-destructive">*</span></Label>
            <Input
              id="modal-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={signingUp}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="modal-password">Password <span className="text-destructive">*</span></Label>
            <Input
              id="modal-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              disabled={signingUp}
            />
            <p className="text-xs text-muted-foreground">Must be at least 8 characters</p>
          </div>

          <Button
            type="submit"
            className="w-full bg-gradient-to-r from-primary to-secondary"
            disabled={signingUp || finalizing}
          >
            {finalizing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Finalizing your resume...
              </>
            ) : signingUp ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating account...
              </>
            ) : (
              <>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Sign up & Download Resume
              </>
            )}
          </Button>
        </form>

        <div className="relative mt-4">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4">
          <Button variant="outline" className="w-full" disabled={signingUp}>
            <Github className="mr-2 h-4 w-4" />
            GitHub
          </Button>
          <Button variant="outline" className="w-full" disabled={signingUp}>
            <Mail className="mr-2 h-4 w-4" />
            Google
          </Button>
        </div>

        <div className="text-center text-sm text-muted-foreground mt-4">
          Already have an account?{' '}
          <button
            type="button"
            onClick={() => setActiveTab('login')}
            className="text-primary hover:underline font-semibold"
          >
            Log in
          </button>
        </div>
        </TabsContent>

          {/* Log In Tab */}
          <TabsContent value="login" className="space-y-4 mt-4">
            <form onSubmit={handleLoginSubmit(handleLogin)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="login-email">Email <span className="text-destructive">*</span></Label>
                <Input
                  id="login-email"
                  type="email"
                  placeholder="you@example.com"
                  {...registerLogin('email')}
                  disabled={loggingIn || finalizing}
                />
                {loginErrors.email && (
                  <p className="text-xs text-destructive">{loginErrors.email.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="login-password">Password <span className="text-destructive">*</span></Label>
                <Input
                  id="login-password"
                  type="password"
                  placeholder="••••••••"
                  {...registerLogin('password')}
                  disabled={loggingIn || finalizing}
                />
                {loginErrors.password && (
                  <p className="text-xs text-destructive">{loginErrors.password.message}</p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-primary to-secondary"
                disabled={loggingIn || finalizing}
              >
                {finalizing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving your resume...
                  </>
                ) : loggingIn ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Logging in...
                  </>
                ) : (
                  <>
                    <LogIn className="mr-2 h-4 w-4" />
                    {hasGuestData ? 'Log in & Save Resume' : 'Log In'}
                  </>
                )}
              </Button>
            </form>

            <div className="text-center text-sm text-muted-foreground mt-4">
              Don&apos;t have an account?{' '}
              <button
                type="button"
                onClick={() => setActiveTab('signup')}
                className="text-primary hover:underline font-semibold"
              >
                Sign up
              </button>
            </div>
          </TabsContent>
        </Tabs>

        <div className="pt-4 border-t mt-4">
          <Button
            variant="ghost"
            className="w-full"
            onClick={() => onOpenChange(false)}
            disabled={signingUp || loggingIn || finalizing}
          >
            Continue as guest
            <span className="text-xs text-muted-foreground ml-2">(can&apos;t download)</span>
          </Button>
        </div>
      </DialogContent>
    </Dialog>
    </>
  );
}

