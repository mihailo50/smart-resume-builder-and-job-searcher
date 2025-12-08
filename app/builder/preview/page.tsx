'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Download, FileText, Share2, CheckCircle2, Loader2, Settings2, Edit, ArrowLeft } from 'lucide-react';
import confetti from 'canvas-confetti';
import { api } from '@/lib/api';
import { TemplateSelector } from '@/components/resume/template-selector';
import { TEMPLATES, FONT_COMBINATIONS, type TemplateId, type FontCombination } from '@/lib/templates';
import { toast } from 'sonner';

interface ResumeData {
  id: string;
  full_name?: string;
  title?: string;
  summary?: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  experiences?: Array<{
    id: string;
    position: string;
    company: string;
    location?: string;
    start_date: string;
    end_date?: string;
    is_current: boolean;
    description?: string;
  }>;
  educations?: Array<{
    id: string;
    degree: string;
    field_of_study?: string;
    institution: string;
    start_date: string;
    end_date?: string;
    is_current: boolean;
    description?: string;
  }>;
  skills?: Array<{
    id: string;
    name: string;
    category?: string;
    level?: string;
  }>;
  projects?: Array<{
    id: string;
    name: string;
    description?: string;
    url?: string;
  }>;
  certifications?: Array<{
    id: string;
    name: string;
    issuer?: string;
    issue_date?: string;
  }>;
}

export default function PreviewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  
  const [resume, setResume] = useState<ResumeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateId>('modern-indigo');
  const [selectedFont, setSelectedFont] = useState<FontCombination>(FONT_COMBINATIONS[0]);
  const [atsMode, setAtsMode] = useState(false);
  const [photoUrl, setPhotoUrl] = useState<string>('');
  
  const openExport = searchParams.get('openExport');

  useEffect(() => {
    if (openExport === 'true' && !loading && resume) {
      setShowExportDialog(true);
    }
  }, [openExport, loading, resume]);
  
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  // Load saved preferences from resume
  useEffect(() => {
    if (resume) {
      // Try to load saved template/font/ats_mode from resume metadata
      const savedTemplate = (resume as any).last_template;
      const savedFont = (resume as any).last_font;
      const savedAtsMode = (resume as any).ats_mode;
      const savedPhotoUrl = (resume as any).photo_url;
      
      if (savedTemplate && TEMPLATES.find(t => t.id === savedTemplate)) {
        setSelectedTemplate(savedTemplate as TemplateId);
      }
      if (savedFont) {
        const font = FONT_COMBINATIONS.find(f => f.heading === savedFont || f.label === savedFont);
        if (font) {
          setSelectedFont(font);
        } else {
          // Map string values
          const fontMap: Record<string, FontCombination> = {
            'modern': FONT_COMBINATIONS[0],
            'classic': FONT_COMBINATIONS[1],
            'creative': FONT_COMBINATIONS[2],
          };
          setSelectedFont(fontMap[savedFont] || FONT_COMBINATIONS[0]);
        }
      }
      if (savedAtsMode !== undefined) {
        setAtsMode(savedAtsMode);
      }
      if (savedPhotoUrl) {
        setPhotoUrl(savedPhotoUrl);
      }
    }
  }, [resume]);
  
  // Load resume data
  useEffect(() => {
    if (!resumeId) {
      toast.error('No resume ID provided');
      router.push('/dashboard');
      return;
    }
    
    const loadResume = async () => {
      try {
        setLoading(true);
        const data = await api.get<ResumeData>(`/v1/resumes/${resumeId}/`);
        setResume(data);
      } catch (error: any) {
        console.error('Failed to load resume:', error);
        const errorMessage = error?.message || 'Failed to load resume';
        toast.error(errorMessage, {
          description: errorMessage.includes('Network error') 
            ? 'Please ensure the backend server is running and accessible.'
            : 'Please try again or contact support if the issue persists.',
          duration: 5000,
        });
        // Don't redirect immediately - let user see the error
        setTimeout(() => {
          router.push('/dashboard');
        }, 3000);
      } finally {
        setLoading(false);
      }
    };
    
    loadResume();
  }, [resumeId, router]);

  const handleExport = async (format: 'pdf' | 'docx') => {
    if (!resumeId || !resume) {
      toast.error('Resume data not available');
      return;
    }

    setExporting(true);
    try {
      // Map font combination to backend format
      let fontValue = 'modern';
      if (typeof selectedFont === 'string') {
        fontValue = selectedFont;
      } else {
        const fontHeading = selectedFont.heading || '';
        if (fontHeading.includes('Inter')) {
          fontValue = 'modern';
        } else if (fontHeading.includes('Roboto')) {
          fontValue = 'classic';
        } else if (fontHeading.includes('Space') || fontHeading.includes('Poppins') || fontHeading.includes('Lato') || fontHeading.includes('Open Sans')) {
          fontValue = 'creative';
        }
      }
      
      const token = localStorage.getItem('auth_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      
      const response = await fetch(`${apiUrl}/v1/resumes/${resumeId}/export/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          format,
          template: selectedTemplate,
          font: fontValue,
          ats_mode: atsMode,
          photo_url: photoUrl || undefined,
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Export failed:', response.status, errorText);
        throw new Error(`Export failed: ${response.status} ${response.statusText}`);
      }
      
      const blob = await response.blob();
      console.log('Blob received:', blob.size, 'bytes, type:', blob.type);
      
      // Create a blob URL that is persistent
      const blobUrl = window.URL.createObjectURL(blob);
      setDownloadUrl(blobUrl);
      
      // Strategy 1: Standard Anchor Click (Hidden)
      const filename = `${resume.title || 'Resume'}_${selectedTemplate}.${format}`;
      const a = document.createElement("a");
      a.style.display = 'none';
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup after delay
      setTimeout(() => {
        document.body.removeChild(a);
        // Do NOT revoke the URL yet so the manual button works
      }, 100);
      
      setShowExportDialog(false);
      toast.success('Resume ready! If download didn\'t start, click the button below.');
    } catch (error: any) {
      console.error('Export failed:', error);
      toast.error(error?.message || `Failed to export ${format.toUpperCase()}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8 text-center"
            >
              <h1 className="text-4xl md:text-5xl font-bold mb-4">Resume Preview</h1>
              <p className="text-xl text-muted-foreground">
                Review your resume and export in your preferred format
              </p>
            </motion.div>

            {loading ? (
              <Card className="mb-6">
                <CardContent className="p-8">
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <span className="ml-3 text-muted-foreground">Loading resume...</span>
                  </div>
                </CardContent>
              </Card>
            ) : resume ? (
              <>
                <Card className="mb-6">
                  <CardContent className="p-8">
                    <div className="space-y-6">
                      {/* Header */}
                      <div>
                        <h2 className="text-2xl font-bold mb-2">
                          {resume.full_name || 'Your Name'}
                        </h2>
                        {resume.title && (
                          <p className="text-muted-foreground text-lg">{resume.title}</p>
                        )}
                        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-sm text-muted-foreground">
                          {resume.email && <span>{resume.email}</span>}
                          {resume.phone && <span>{resume.phone}</span>}
                          {resume.location && <span>{resume.location}</span>}
                        </div>
                        {(resume.linkedin_url || resume.github_url || resume.portfolio_url) && (
                          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-sm">
                            {resume.linkedin_url && (
                              <a href={resume.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                LinkedIn
                              </a>
                            )}
                            {resume.github_url && (
                              <a href={resume.github_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                GitHub
                              </a>
                            )}
                            {resume.portfolio_url && (
                              <a href={resume.portfolio_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                Portfolio
                              </a>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Summary */}
                      {resume.summary && (
                        <div>
                          <h3 className="text-lg font-semibold mb-2">Summary</h3>
                          <p className="text-sm text-muted-foreground whitespace-pre-line">{resume.summary}</p>
                        </div>
                      )}

                      {/* Experience */}
                      {resume.experiences && resume.experiences.length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold mb-3">Experience</h3>
                          <div className="space-y-4">
                            {resume.experiences.map((exp) => (
                              <div key={exp.id}>
                                <div className="flex justify-between items-start mb-1">
                                  <div>
                                    <span className="font-semibold">{exp.position}</span>
                                    {exp.company && (
                                      <>
                                        {' '}at{' '}
                                        <span className="font-semibold">{exp.company}</span>
                                      </>
                                    )}
                                    {exp.location && <span className="text-muted-foreground"> • {exp.location}</span>}
                                  </div>
                                  <span className="text-sm text-muted-foreground whitespace-nowrap ml-4">
                                    {new Date(exp.start_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                                    {' – '}
                                    {exp.is_current
                                      ? 'Present'
                                      : exp.end_date
                                      ? new Date(exp.end_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
                                      : 'Present'}
                                  </span>
                                </div>
                                {exp.description && (
                                  <p className="text-sm text-muted-foreground whitespace-pre-line">{exp.description}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Education */}
                      {resume.educations && resume.educations.length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold mb-3">Education</h3>
                          <div className="space-y-3">
                            {resume.educations.map((edu) => (
                              <div key={edu.id}>
                                <div className="flex justify-between items-start">
                                  <div>
                                    <span className="font-semibold">{edu.degree}</span>
                                    {edu.field_of_study && (
                                      <>
                                        {' '}in{' '}
                                        <span className="font-semibold">{edu.field_of_study}</span>
                                      </>
                                    )}
                                    {edu.institution && (
                                      <>
                                        {' '}• <span className="text-muted-foreground">{edu.institution}</span>
                                      </>
                                    )}
                                  </div>
                                  <span className="text-sm text-muted-foreground whitespace-nowrap ml-4">
                                    {new Date(edu.start_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                                    {' – '}
                                    {edu.is_current
                                      ? 'Present'
                                      : edu.end_date
                                      ? new Date(edu.end_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
                                      : 'Present'}
                                  </span>
                                </div>
                                {edu.description && (
                                  <p className="text-sm text-muted-foreground mt-1">{edu.description}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Skills */}
                      {resume.skills && resume.skills.length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold mb-3">Skills</h3>
                          <div className="flex flex-wrap gap-2">
                            {resume.skills.map((skill) => (
                              <span
                                key={skill.id}
                                className="px-3 py-1 bg-secondary text-secondary-foreground rounded-full text-sm"
                              >
                                {skill.name}
                                {skill.level && <span className="ml-1 text-xs opacity-70">({skill.level})</span>}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Projects */}
                      {resume.projects && resume.projects.length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold mb-3">Projects</h3>
                          <div className="space-y-3">
                            {resume.projects.map((project) => (
                              <div key={project.id}>
                                <div className="font-semibold">{project.name}</div>
                                {project.description && (
                                  <p className="text-sm text-muted-foreground mt-1">{project.description}</p>
                                )}
                                {project.url && (
                                  <a
                                    href={project.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-primary hover:underline mt-1 inline-block"
                                  >
                                    View Project →
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Certifications */}
                      {resume.certifications && resume.certifications.length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold mb-3">Certifications</h3>
                          <div className="space-y-2">
                            {resume.certifications.map((cert) => (
                              <div key={cert.id}>
                                <span className="font-semibold">{cert.name}</span>
                                {cert.issuer && (
                                  <>
                                    {' • '}
                                    <span className="text-muted-foreground">{cert.issuer}</span>
                                  </>
                                )}
                                {cert.issue_date && (
                                  <span className="text-sm text-muted-foreground ml-2">
                                    ({new Date(cert.issue_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })})
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Export Buttons */}
                <div className="flex flex-wrap gap-4 justify-center mb-6">
                  <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
                    <DialogTrigger asChild>
                      <Button
                        size="lg"
                        className="bg-gradient-to-r from-primary to-secondary"
                      >
                        <Settings2 className="mr-2 h-5 w-5" />
                        Configure Export
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Export Resume</DialogTitle>
                        <DialogDescription>
                          Choose your template, font, and export options
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-6 mt-4">
                        <TemplateSelector
                          selectedTemplate={selectedTemplate}
                          onTemplateChange={setSelectedTemplate}
                          selectedFont={selectedFont}
                          onFontChange={setSelectedFont}
                          atsMode={atsMode}
                          onAtsModeChange={setAtsMode}
                          photoUrl={photoUrl}
                          onPhotoUrlChange={setPhotoUrl}
                        />
                        <div className="flex gap-3 justify-end pt-4 border-t">
                          <Button
                            onClick={() => handleExport('pdf')}
                            disabled={exporting}
                            className="bg-gradient-to-r from-primary to-secondary"
                          >
                            {exporting ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Exporting...
                              </>
                            ) : (
                              <>
                                <Download className="mr-2 h-4 w-4" />
                                Export PDF
                              </>
                            )}
                          </Button>
                          <Button
                            onClick={() => handleExport('docx')}
                            disabled={exporting}
                            variant="outline"
                          >
                            {exporting ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Exporting...
                              </>
                            ) : (
                              <>
                                <FileText className="mr-2 h-4 w-4" />
                                Export DOCX
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>

                  <Button
                    onClick={() => handleExport('pdf')}
                    disabled={exporting || !resume}
                    size="lg"
                    variant="outline"
                  >
                    {exporting ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Exporting...
                      </>
                    ) : (
                      <>
                        <Download className="mr-2 h-5 w-5" />
                        Quick Export PDF
                      </>
                    )}
                  </Button>
                  <Button
                    onClick={() => router.push(`/builder/personal?id=${resumeId}`)}
                    size="lg"
                    variant="outline"
                  >
                    <Edit className="mr-2 h-5 w-5" />
                    Edit Resume
                  </Button>
                  <Button
                    onClick={() => router.push('/dashboard')}
                    size="lg"
                    variant="ghost"
                  >
                    <ArrowLeft className="mr-2 h-5 w-5" />
                    Back to Dashboard
                  </Button>
                </div>
                
                {downloadUrl && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mt-4 p-4 bg-muted/30 rounded-lg border border-border/50 max-w-md mx-auto"
                  >
                    <p className="text-sm text-muted-foreground mb-3">
                      Download didn't start automatically?
                    </p>
                    <Button 
                      variant="default"
                      onClick={() => {
                        const a = document.createElement("a");
                        a.href = downloadUrl;
                        a.download = `${resume.title || 'Resume'}_${selectedTemplate}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                      }}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Click here to download manually
                    </Button>
                  </motion.div>
                )}
              </>
            ) : (
              <Card className="mb-6">
                <CardContent className="p-8">
                  <div className="text-center py-12">
                    <p className="text-muted-foreground mb-4">Resume not found</p>
                    <Button onClick={() => router.push('/dashboard')} variant="outline">
                      Go to Dashboard
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </PageTransition>
  );
}


