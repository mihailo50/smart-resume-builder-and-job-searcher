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
import { useManualDirtyGuard, useBeforeUnloadGuard, clearDirtyState } from '@/lib/use-dirty-guard';

interface Certification {
  id: string;
  title: string;
  issuer: string;
  issueDate: string;
  expirationDate: string;
  credentialId: string;
  url: string;
  description: string;
  doesNotExpire: boolean;
}

function CertificationsContent() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState(45); // Step 5 of 11
  const [initialCertifications, setInitialCertifications] = useState<Certification[]>([]);
  
  // Track dirty state
  const { markDirty, markClean } = useManualDirtyGuard('certifications');
  useBeforeUnloadGuard(!isAuthenticated()); // Only for guest users

  // Track changes to certifications array
  useEffect(() => {
    if (initialCertifications.length === 0 && certifications.length === 0) return;
    
    const isDirty = JSON.stringify(certifications) !== JSON.stringify(initialCertifications);
    if (isDirty) {
      markDirty();
    } else {
      markClean();
    }
  }, [certifications, initialCertifications, markDirty, markClean]);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    if (guestId || (!resumeId && !isAuthenticated())) {
      // Guest mode - load from localStorage
      loadGuestCertifications();
    } else if (resumeId && isAuthenticated()) {
      // Authenticated mode - load from API
      loadCertifications();
    }
  }, [resumeId, guestId]);

  const loadCertifications = async () => {
    if (!resumeId) return;
    
    try {
      setLoading(true);
      const data = await api.get<any[]>(`/v1/resumes/${resumeId}/certifications/`);
      const loadedCertifications = data.map((cert: any) => ({
        id: cert.id,
        title: cert.title || cert.name || '',
        issuer: cert.issuer || '',
        issueDate: cert.issue_date ? new Date(cert.issue_date).toISOString().slice(0, 7) : '',
        expirationDate: cert.expiration_date || cert.expiry_date ? (cert.expiration_date || cert.expiry_date ? new Date(cert.expiration_date || cert.expiry_date).toISOString().slice(0, 7) : '') : '',
        credentialId: cert.credential_id || '',
        url: cert.url || cert.credential_url || '',
        description: cert.description || '',
        doesNotExpire: !(cert.expiration_date || cert.expiry_date),
      }));
      setCertifications(loadedCertifications);
      setInitialCertifications(JSON.parse(JSON.stringify(loadedCertifications))); // Deep copy
    } catch (error: any) {
      console.error('Failed to load certifications:', error);
      toast.error('Failed to load certifications');
    } finally {
      setLoading(false);
    }
  };

  const loadGuestCertifications = () => {
    try {
      const guestData = loadGuestResume();
      if (guestData.certifications && guestData.certifications.length > 0) {
        const loadedCertifications = guestData.certifications.map((cert: any) => ({
          id: cert.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
          title: cert.title || '',
          issuer: cert.issuer || '',
          issueDate: cert.issueDate || '',
          expirationDate: cert.expirationDate || '',
          credentialId: cert.credentialId || '',
          url: cert.url || '',
          description: cert.description || '',
          doesNotExpire: cert.doesNotExpire || !cert.expirationDate,
        }));
        setCertifications(loadedCertifications);
        setInitialCertifications(JSON.parse(JSON.stringify(loadedCertifications))); // Deep copy
      }
    } catch (error) {
      console.error('Failed to load guest certifications:', error);
    }
  };

  const addCertification = () => {
    setCertifications([
      ...certifications,
      {
        id: Date.now().toString(),
        title: '',
        issuer: '',
        issueDate: '',
        expirationDate: '',
        credentialId: '',
        url: '',
        description: '',
        doesNotExpire: false,
      },
    ]);
  };

  const removeCertification = (id: string) => {
    setCertifications(certifications.filter((cert) => cert.id !== id));
  };

  const updateCertification = (id: string, field: keyof Certification, value: string | boolean) => {
    setCertifications(
      certifications.map((cert) => {
        if (cert.id === id) {
          const updated = { ...cert, [field]: value };
          // If "does not expire" is checked, clear expiration date
          if (field === 'doesNotExpire' && value === true) {
            updated.expirationDate = '';
          }
          return updated;
        }
        return cert;
      })
    );
  };

  const saveCertificationsToAPI = async () => {
    if (!resumeId) return;
    
    // Get existing certifications from backend
    const existingCertifications = await api.get<any[]>(`/v1/resumes/${resumeId}/certifications/`);
    const existingIds = new Set(existingCertifications.map((cert: any) => cert.id));

    // Save/update each certification
    for (const cert of certifications) {
      const certificationData: Record<string, any> = {
        title: cert.title,  // Serializer will map this to 'name'
        issuer: cert.issuer || '',
        issue_date: cert.issueDate ? `${cert.issueDate}-01` : undefined,
        expiration_date: cert.doesNotExpire ? null : (cert.expirationDate ? `${cert.expirationDate}-01` : null),  // Serializer will map this to 'expiry_date'
        credential_id: cert.credentialId || '',
        url: cert.url || '',  // Serializer will map this to 'credential_url'
        description: cert.description || '',
        order: certifications.indexOf(cert),
      };
      
      // Filter out empty strings
      const filteredData = Object.fromEntries(
        Object.entries(certificationData).filter(([_, v]) => v !== '' && v !== undefined)
      );
      
      if (cert.id && existingIds.has(cert.id)) {
        // Update existing
        await api.put(`/v1/resumes/${resumeId}/certifications/${cert.id}/`, filteredData);
      } else {
        // Create new
        await api.post(`/v1/resumes/${resumeId}/certifications/`, filteredData);
      }
    }

    // Delete removed certifications
    for (const existing of existingCertifications) {
      if (!certifications.some((cert) => cert.id === existing.id)) {
        await api.delete(`/v1/resumes/${resumeId}/certifications/${existing.id}/`);
      }
    }
  };

  const handleNext = async () => {
    try {
      setSaving(true);

      if (guestId || (!resumeId && !isAuthenticated())) {
        // Guest flow - save to localStorage
        saveGuestResume({
          certifications: certifications.map((cert, index) => ({
            id: cert.id,
            title: cert.title,
            issuer: cert.issuer,
            issueDate: cert.issueDate,
            expirationDate: cert.doesNotExpire ? '' : cert.expirationDate,
            credentialId: cert.credentialId,
            url: cert.url,
            description: cert.description,
            doesNotExpire: cert.doesNotExpire,
            order: index,
          })),
        });
        
        const currentGuestId = getGuestResumeId();
        toast.success('Certifications saved');
        clearDirtyState(); // Clear dirty state after successful save
        router.push(`/builder/skills?guestId=${currentGuestId}`);
        return;
      }

      // Authenticated flow - save to API (already handled above)
      await saveCertificationsToAPI();
      
      toast.success('Certifications saved');
      clearDirtyState(); // Clear dirty state after successful save
      router.push(`/builder/skills?id=${resumeId}`);
    } catch (error: any) {
      console.error('Failed to save certifications:', error);
      toast.error(error?.message || 'Failed to save certifications');
    } finally {
      setSaving(false);
    }
  };

  const steps = [
    { id: 1, name: 'Personal Info', href: '/builder/personal', current: false },
    { id: 2, name: 'Experience', href: '/builder/experience', current: false },
    { id: 3, name: 'Projects', href: '/builder/projects', current: false },
    { id: 4, name: 'Education', href: '/builder/education', current: false },
    { id: 5, name: 'Certifications', href: '/builder/certifications', current: true },
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
                  Step {steps[4].id} of {steps.length}
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
                      <CardTitle>Certifications</CardTitle>
                      <Button type="button" onClick={addCertification} variant="outline" size="sm">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Certification
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="ml-3 text-muted-foreground">Loading certifications...</span>
                      </div>
                    ) : certifications.length === 0 ? (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground mb-4">No certifications added yet</p>
                        <Button type="button" onClick={addCertification} variant="outline">
                          <Plus className="mr-2 h-4 w-4" />
                          Add Your First Certification
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        <AnimatePresence>
                          {certifications.map((certification, index) => (
                            <motion.div
                              key={certification.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -20 }}
                            >
                              <Card>
                                <CardHeader>
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Certification #{index + 1}</CardTitle>
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => removeCertification(certification.id)}
                                    >
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2 md:col-span-2">
                                      <Label>
                                        Certification Title <span className="text-destructive">*</span>
                                      </Label>
                                      <Input
                                        placeholder="AWS Certified Solutions Architect"
                                        value={certification.title}
                                        onChange={(e) =>
                                          updateCertification(certification.id, 'title', e.target.value)
                                        }
                                        required
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Issuing Organization</Label>
                                      <Input
                                        placeholder="Amazon Web Services"
                                        value={certification.issuer}
                                        onChange={(e) =>
                                          updateCertification(certification.id, 'issuer', e.target.value)
                                        }
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Issue Date</Label>
                                      <Input
                                        type="month"
                                        value={certification.issueDate}
                                        onChange={(e) =>
                                          updateCertification(certification.id, 'issueDate', e.target.value)
                                        }
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Credential ID</Label>
                                      <Input
                                        placeholder="ABC123XYZ"
                                        value={certification.credentialId}
                                        onChange={(e) =>
                                          updateCertification(certification.id, 'credentialId', e.target.value)
                                        }
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Verification URL</Label>
                                      <Input
                                        type="url"
                                        placeholder="https://example.com/verify"
                                        value={certification.url}
                                        onChange={(e) =>
                                          updateCertification(certification.id, 'url', e.target.value)
                                        }
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Expiration Date</Label>
                                      <Input
                                        type="month"
                                        value={certification.expirationDate}
                                        onChange={(e) =>
                                          updateCertification(certification.id, 'expirationDate', e.target.value)
                                        }
                                        disabled={certification.doesNotExpire}
                                      />
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <Checkbox
                                        id={`no-expire-${certification.id}`}
                                        checked={certification.doesNotExpire}
                                        onCheckedChange={(checked) =>
                                          updateCertification(certification.id, 'doesNotExpire', !!checked)
                                        }
                                      />
                                      <Label
                                        htmlFor={`no-expire-${certification.id}`}
                                        className="cursor-pointer"
                                      >
                                        Does not expire
                                      </Label>
                                    </div>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Description</Label>
                                    <Textarea
                                      placeholder="Describe the certification and its relevance..."
                                      rows={3}
                                      value={certification.description}
                                      onChange={(e) =>
                                        updateCertification(certification.id, 'description', e.target.value)
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
                            ? `/builder/education?id=${resumeId}` 
                            : guestId 
                            ? `/builder/education?guestId=${guestId}` 
                            : '/builder/education'
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
                            Next: Skills
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

export default function CertificationsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <CertificationsContent />
    </Suspense>
  );
}
