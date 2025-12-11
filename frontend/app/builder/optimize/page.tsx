'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { useGuestGuard } from '@/lib/use-guest-guard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Sparkles,
  TrendingUp,
  FileText,
  CheckCircle2,
  AlertCircle,
  Zap,
  ArrowRight,
  Download,
  Upload,
  Loader2,
  Info,
} from 'lucide-react';
import confetti from 'canvas-confetti';
import Link from 'next/link';
import { 
  getGuestResumeId, 
  isAuthenticated, 
  loadGuestResume, 
  saveGuestResume,
} from '@/lib/guest-resume';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { convertResumeToText, hasResumeContent } from '@/lib/resume-to-text';

interface AnalysisResult {
  ats_score: number;
  missing_keywords: string[];
  suggestions: Array<{
    type: string;
    text: string;
    priority?: string;
  }>;
  readability_score?: number;
  bullet_strength?: number;
  quantifiable_achievements?: number;
  matched_keywords?: string[];
}

function OptimizeContent() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [atsScore, setAtsScore] = useState<number | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [resumeText, setResumeText] = useState('');
  const [jobDesc, setJobDesc] = useState('');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [optimizationApplied, setOptimizationApplied] = useState(false);
  const [draftData, setDraftData] = useState<any>(null);
  const [hasDraftContent, setHasDraftContent] = useState(false);
  const [isDraftEmpty, setIsDraftEmpty] = useState(true);
  const linkedInFileInputRef = useRef<HTMLInputElement>(null);

  // Check if optimized text exists on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const guestData = loadGuestResume();
      if (guestData.optimizedSummary) {
        setOptimizationApplied(true);
      }
    }
  }, []);
  const [error, setError] = useState<string | null>(null);

  // Load resume data from guest storage or API on mount
  useEffect(() => {
    const loadResumeData = async () => {
      if (typeof window === 'undefined') return;
      
      try {
        if (guestId || (!resumeId && !isAuthenticated())) {
          // Guest mode - load from localStorage
          const guestData = loadGuestResume();
          setDraftData(guestData);
          const hasContent = hasResumeContent(guestData);
          setHasDraftContent(hasContent);
          setIsDraftEmpty(!hasContent);
          if (guestData.personal?.summary) {
            setResumeText(guestData.personal.summary || '');
          }
        } else if (resumeId && isAuthenticated()) {
          // Authenticated mode - try to load from API
          try {
            const resume = await api.get<{ 
              title?: string;
              summary?: string;
              optimized_summary?: string;
              experiences?: any[];
              educations?: any[];
              skills?: any[];
              projects?: any[];
              certifications?: any[];
            }>(`/v1/resumes/${resumeId}/`);
            
            // Load related data
            const [experiences, educations, skills, projects, certifications] = await Promise.all([
              api.get(`/v1/resumes/${resumeId}/experiences/`).catch(() => []),
              api.get(`/v1/resumes/${resumeId}/educations/`).catch(() => []),
              api.get(`/v1/resumes/${resumeId}/skills/`).catch(() => []),
              api.get(`/v1/resumes/${resumeId}/projects/`).catch(() => []),
              api.get(`/v1/resumes/${resumeId}/certifications/`).catch(() => []),
            ]);
            
            const structuredData = {
              personal: {
                fullName: resume.title,
                summary: resume.optimized_summary || resume.summary,
              },
              experiences: experiences || [],
              educations: educations || [],
              skills: skills || [],
              projects: projects || [],
              certifications: certifications || [],
              optimizedSummary: resume.optimized_summary,
            };
            
            setDraftData(structuredData);
            const hasContent = hasResumeContent(structuredData);
            setHasDraftContent(hasContent);
            setIsDraftEmpty(!hasContent);
            
            if (resume?.optimized_summary || resume?.summary) {
              setResumeText(resume.optimized_summary || resume.summary || '');
            }
          } catch (error) {
            console.warn('Could not load resume from API:', error);
            setIsDraftEmpty(true);
            setHasDraftContent(false);
          }
        } else {
          // No resumeId and not authenticated - check if we have any data
          setIsDraftEmpty(true);
          setHasDraftContent(false);
        }
      } catch (error) {
        console.error('Failed to load resume data:', error);
        setIsDraftEmpty(true);
        setHasDraftContent(false);
      }
    };
    
    loadResumeData();
  }, [resumeId, guestId]);
  
  // Update isDraftEmpty when draftData changes (but not when resumeText changes from imports)
  useEffect(() => {
    if (draftData) {
      const hasContent = hasResumeContent(draftData);
      setHasDraftContent(hasContent);
      // Only set empty if no draft content AND no imported text
      setIsDraftEmpty(!hasContent && !resumeText.trim());
    } else {
      setIsDraftEmpty(!resumeText.trim());
    }
  }, [draftData]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'];
    const allowedExtensions = ['.pdf', '.docx', '.doc'];
    const fileName = file.name.toLowerCase();
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.some(ext => fileName.endsWith(ext))) {
      toast.error('Please upload a PDF or DOCX file');
      return;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      toast.error('File too large. Maximum size is 10MB');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('file', file);

      // Call parse endpoint using api client but with FormData
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      const parseUrl = `${apiUrl.endsWith('/api') ? apiUrl : apiUrl + '/api'}/v1/ai/parse-resume-file/`;
      
      const response = await fetch(parseUrl, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to parse file');
      }

      if (data.success && data.text) {
        setResumeText(data.text);
        setIsDraftEmpty(false); // File was uploaded, so draft is no longer empty
        toast.success('File parsed successfully! Click "Analyze My Resume" to continue.');
      } else {
        throw new Error('No text extracted from file');
      }
    } catch (error: any) {
      console.error('File upload error:', error);
      const errorMessage = error.message || 'Failed to parse file. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleLinkedInImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type (PDF only for LinkedIn)
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Please upload a PDF file');
      return;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      toast.error('File too large. Maximum size is 10MB');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('file', file);

      // Call parse endpoint
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      const parseUrl = `${apiUrl.endsWith('/api') ? apiUrl : apiUrl + '/api'}/v1/ai/parse-resume-file/`;
      
      const response = await fetch(parseUrl, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to parse LinkedIn resume');
      }

      if (data.success && data.text) {
        // Parse LinkedIn PDF and populate sections
        // For now, just set the text - future enhancement can parse structured data
        setResumeText(data.text);
        setIsDraftEmpty(false); // LinkedIn file was uploaded, so draft is no longer empty
        toast.success('LinkedIn resume imported! Review and populate sections manually.');
        
        // TODO: Implement automatic section population from LinkedIn PDF
        // This would require enhanced parsing logic in the backend
      } else {
        throw new Error('No text extracted from LinkedIn resume');
      }
    } catch (error: any) {
      console.error('LinkedIn import error:', error);
      const errorMessage = error.message || 'Failed to import LinkedIn resume. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setUploading(false);
      // Reset file input
      if (linkedInFileInputRef.current) {
        linkedInFileInputRef.current.value = '';
      }
    }
  };

  const handleOptimizeDraft = async () => {
    if (!draftData || !hasDraftContent) {
      toast.error('Complete previous steps first or import an existing resume');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysisResult(null);

    try {
      // Convert structured data to text
      const convertedText = convertResumeToText(draftData);
      setResumeText(convertedText);

      // Prepare request data
      const requestData: any = {
        resume_text: convertedText,
      };

      // Add job description if provided
      if (jobDesc.trim()) {
        requestData.job_desc = jobDesc.trim();
      }

      // Add resume_id if authenticated and available
      if (resumeId && isAuthenticated()) {
        requestData.resume_id = resumeId;
      }

      // Call analyze endpoint
      const response = await api.post<AnalysisResult>('v1/ai/analyze-resume/', requestData);

      if (response) {
        setAtsScore(response.ats_score);
        setAnalysisResult(response);
        
        // Confetti animation
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#6366f1', '#8b5cf6'],
        });

        toast.success('Resume analyzed successfully!');
      } else {
        throw new Error('No analysis results received');
      }
    } catch (error: any) {
      console.error('Analysis error:', error);
      
      if (error?.response?.detail) {
        const detailMessage = error.response.detail;
        setError(detailMessage);
        toast.error(detailMessage, { duration: 5000 });
        return;
      }
      
      let errorMessage = 'Failed to analyze resume. Please try again.';
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
      
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAnalyze = async () => {
    // Check if guest has already used AI analysis
    if (!resumeText.trim()) {
      toast.error('Please paste your resume text or upload a file first');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysisResult(null);

    try {
      // Prepare request data
      const requestData: any = {
        resume_text: resumeText,
      };

      // Add job description if provided
      if (jobDesc.trim()) {
        requestData.job_desc = jobDesc.trim();
      }

      // Add resume_id if authenticated and available
      if (resumeId && isAuthenticated()) {
        requestData.resume_id = resumeId;
      }

      // Call analyze endpoint
      const response = await api.post<AnalysisResult>('v1/ai/analyze-resume/', requestData);

      if (response) {
        setAtsScore(response.ats_score);
        setAnalysisResult(response);
        
        // Mark AI analysis as used for guests
        // Confetti animation
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#6366f1', '#8b5cf6'],
        });

        toast.success('Resume analyzed successfully!');
      } else {
        throw new Error('No analysis results received');
      }
    } catch (error: any) {
      console.error('Analysis error:', error);
      
      if (error?.response?.detail) {
        const detailMessage = error.response.detail;
        setError(detailMessage);
        toast.error(detailMessage, { duration: 5000 });
        return;
      }
      
      let errorMessage = 'Failed to analyze resume. Please try again.';
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
      
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setAnalyzing(false);
    }
  };

  const suggestions = analysisResult?.suggestions || [];
  const missingKeywords = analysisResult?.missing_keywords || [];
  const [applying, setApplying] = useState(false);

  const applyAllSuggestions = async () => {
    if (!resumeText.trim() || !analysisResult || suggestions.length === 0) {
      toast.error('No resume text or suggestions available');
      return;
    }

    setApplying(true);
    setError(null);

    try {
      // Call AI endpoint to apply all suggestions
      const response = await api.post<{
        optimized_text: string;
        changes_applied?: string[];
      }>('v1/ai/apply-suggestions/', {
        resume_text: resumeText,
        suggestions: suggestions,
        missing_keywords: missingKeywords,
      });

      if (response.optimized_text) {
        // Update the resume text with AI-optimized version
        setResumeText(response.optimized_text);
        
        // Clear previous analysis to encourage re-analysis
        setAtsScore(null);
        setAnalysisResult(null);
        
        // Save to guest storage if guest mode
        if (guestId || (!resumeId && !isAuthenticated())) {
          const guestData = loadGuestResume();
          saveGuestResume({
            personal: {
              ...(guestData.personal || {}),
            },
            optimizedSummary: response.optimized_text,  // Primary field
          });
        } else if (resumeId && isAuthenticated()) {
          try {
            await api.put(`/v1/resumes/${resumeId}/optimized-summary/`, {
              optimized_summary: response.optimized_text,
            });
          } catch (error) {
            console.warn('Could not save optimized resume to API:', error);
          }
        }

        // Mark optimization as applied in state
        setOptimizationApplied(true);

        // Show success message with changes applied
        const changesMsg = response.changes_applied 
          ? response.changes_applied.join('. ') 
          : 'All suggestions applied using AI';
        toast.success('All suggestions applied! Review the optimized resume text.', {
          description: changesMsg,
          duration: 5000,
        });
        
        // Scroll to top of textarea to show changes
        const textarea = document.getElementById('resume-text');
        if (textarea) {
          textarea.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // Highlight the textarea briefly
          textarea.focus();
          setTimeout(() => {
            textarea.blur();
          }, 1000);
        }
        
        // Suggest re-analysis
        setTimeout(() => {
          toast.info('Click "Analyze My Resume" again to see your improved ATS score!', {
            duration: 6000,
          });
        }, 2500);
      } else {
        throw new Error('No optimized text received from server');
      }

    } catch (error: any) {
      console.error('Failed to apply suggestions:', error);
      
      if (error?.response?.detail) {
        const detailMessage = error.response.detail;
        setError(detailMessage);
        toast.error(detailMessage, { duration: 5000 });
        return;
      }
      
      let errorMessage = 'Failed to apply suggestions. Please try again.';
      
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
      
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setApplying(false);
    }
  };

  return (
    <TooltipProvider>
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-[800px] mx-auto flex flex-col items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8 w-full text-center"
            >
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-center gap-2 flex-wrap">
                  <h1 className="text-4xl md:text-5xl font-bold">
                    Optimize your entire resume for a specific job
                  </h1>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        aria-label="Summary vs optimization"
                        className="text-muted-foreground hover:text-primary transition-colors"
                      >
                        <Info className="h-5 w-5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Summary = your professional profile. Optimization = full resume rewrite with job keywords.</p>
                    </TooltipContent>
                  </Tooltip>
                </div>
                <p className="text-xl text-muted-foreground">
                  Get instant ATS score improvements with AI-powered suggestions
                </p>
                <p className="text-sm text-muted-foreground">
                  Optimize your resume for specific job postings with targeted keyword analysis. This step is optional if you&apos;re importing an existing resume.
                </p>
              </div>
            </motion.div>

            {/* Empty Draft State - Show if no draft data exists */}
            {!hasDraftContent && !resumeText.trim() && !uploading ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full mb-8"
              >
                <Card className="border-2 border-dashed border-muted">
                  <CardContent className="pt-6 pb-6 text-center">
                    <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">Build your resume first!</h3>
                    <p className="text-muted-foreground mb-6">
                      Complete the previous steps to build your resume, then come back here to optimize it with AI.
                    </p>
                    <Button 
                      asChild
                      size="lg"
                      className="bg-gradient-to-r from-primary to-secondary"
                    >
                      <Link href={
                        resumeId 
                          ? `/builder/personal?id=${resumeId}` 
                          : guestId 
                          ? `/builder/personal?guestId=${guestId}` 
                          : '/builder/personal'
                      }>
                        Start Building Resume
                        <ArrowRight className="ml-2 h-5 w-5" />
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ) : (
              <div className="w-full space-y-6">
                {/* Main Optimization Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="w-full"
                >
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-primary" />
                        Optimize Your Resume
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      {/* Job Description Textarea */}
                      <div className="space-y-2">
                        <label htmlFor="job-desc" className="text-sm font-medium">
                          Job Description (Optional - for targeted keyword analysis)
                        </label>
                        <Textarea
                          id="job-desc"
                          placeholder="Paste the job description here to get targeted keyword suggestions..."
                          rows={6}
                          value={jobDesc}
                          onChange={(e) => setJobDesc(e.target.value)}
                          className="min-h-[150px]"
                        />
                        <p className="text-xs text-muted-foreground">
                          {jobDesc.length} characters. Adding a job description will help identify missing keywords and improve ATS score.
                        </p>
                      </div>

                      {/* Primary Action: Optimize Current Draft - Show if draft has data */}
                      {hasDraftContent ? (
                        <div className="space-y-4">
                          <Button
                            onClick={handleOptimizeDraft}
                            disabled={analyzing || uploading}
                            className="w-full bg-gradient-to-r from-primary to-secondary h-14 text-lg font-semibold"
                            size="lg"
                          >
                            {analyzing ? (
                              <>
                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                Analyzing Your Draft...
                              </>
                            ) : (
                              <>
                                <Sparkles className="mr-2 h-5 w-5" />
                                Optimize My Current Draft
                              </>
                            )}
                          </Button>
                          <p className="text-sm text-muted-foreground text-center">
                            We&apos;ll convert your structured resume sections into text and analyze them for ATS optimization.
                          </p>
                        </div>
                      ) : (
                        // Show analyze button if user has imported text
                        resumeText.trim() && (
                          <div className="space-y-4">
                            <Button
                              onClick={handleAnalyze}
                              disabled={!resumeText.trim() || analyzing || uploading}
                              className="w-full bg-gradient-to-r from-primary to-secondary h-14 text-lg font-semibold"
                              size="lg"
                            >
                              {analyzing ? (
                                <>
                                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                  Analyzing...
                                </>
                              ) : (
                                <>
                                  <Zap className="mr-2 h-5 w-5" />
                                  Analyze My Resume
                                </>
                              )}
                            </Button>
                            <p className="text-sm text-muted-foreground text-center">
                              Analyzing your imported resume for ATS optimization.
                            </p>
                          </div>
                        )
                      )}

                      {/* Import Options - Accordion (Secondary) */}
                      <div className="pt-4 border-t">
                        <Accordion type="single" collapsible className="w-full">
                          <AccordionItem value="import">
                            <AccordionTrigger className="text-sm font-medium text-muted-foreground">
                              <div className="flex items-center gap-2">
                                <Upload className="h-4 w-4" />
                                Import Instead?
                              </div>
                            </AccordionTrigger>
                            <AccordionContent className="space-y-4 pt-4">
                              <p className="text-xs text-muted-foreground mb-4">
                                If you have an existing resume file or text, you can import it here instead of building from scratch.
                              </p>

                              {/* LinkedIn Import */}
                              <div className="space-y-2">
                                <label className="text-sm font-medium">Import from LinkedIn</label>
                                <input
                                  ref={linkedInFileInputRef}
                                  type="file"
                                  accept=".pdf"
                                  onChange={handleLinkedInImport}
                                  className="hidden"
                                  id="linkedin-upload"
                                />
                                <Button
                                  type="button"
                                  variant="outline"
                                  onClick={() => linkedInFileInputRef.current?.click()}
                                  disabled={uploading}
                                  className="w-full"
                                >
                                  {uploading ? (
                                    <>
                                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                      Importing...
                                    </>
                                  ) : (
                                    <>
                                      <Upload className="mr-2 h-4 w-4" />
                                      Upload LinkedIn PDF Resume
                                    </>
                                  )}
                                </Button>
                                <p className="text-xs text-muted-foreground">
                                  Download your LinkedIn resume as PDF and upload it here to auto-populate sections.
                                </p>
                              </div>

                              {/* Divider */}
                              <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                  <span className="w-full border-t" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                  <span className="bg-background px-2 text-muted-foreground">Or</span>
                                </div>
                              </div>

                              {/* File Upload */}
                              <div className="space-y-2">
                                <label className="text-sm font-medium">Upload Resume File</label>
                                <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center hover:border-primary/50 transition-colors cursor-pointer relative">
                                  <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf,.docx,.doc"
                                    onChange={handleFileUpload}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    disabled={uploading}
                                  />
                                  {uploading ? (
                                    <div className="flex flex-col items-center gap-2">
                                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                      <p className="text-sm text-muted-foreground">Parsing file...</p>
                                    </div>
                                  ) : (
                                    <div className="flex flex-col items-center gap-2">
                                      <Upload className="h-8 w-8 text-muted-foreground" />
                                      <p className="text-sm font-medium">Click to upload or drag and drop</p>
                                      <p className="text-xs text-muted-foreground">PDF or DOCX (max. 10MB)</p>
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Divider */}
                              <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                  <span className="w-full border-t" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                  <span className="bg-background px-2 text-muted-foreground">Or</span>
                                </div>
                              </div>

                              {/* Text Input */}
                              <div className="space-y-2">
                                <label htmlFor="resume-text" className="text-sm font-medium">
                                  Paste Resume Text
                                </label>
                                <Textarea
                                  id="resume-text"
                                  placeholder="Paste your resume text here..."
                                  rows={8}
                                  value={resumeText}
                                  onChange={(e) => {
                                    setResumeText(e.target.value);
                                    // Update empty state when user types
                                    if (e.target.value.trim()) {
                                      setIsDraftEmpty(false);
                                    }
                                  }}
                                  className="min-h-[200px]"
                                />
                                <p className="text-xs text-muted-foreground">
                                  {resumeText.length} characters
                                </p>
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      </div>

                    {/* Error Message */}
                    {error && (
                      <div className="bg-destructive/10 text-destructive p-3 rounded-lg flex items-center gap-2">
                        <AlertCircle className="h-4 w-4" />
                        <span className="text-sm">{error}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
                </motion.div>

                {/* Results Section */}
                {atsScore !== null && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full space-y-6"
                  >
                    {/* ATS Score */}
                    <Card className="border-2 border-primary/20">
                      <CardHeader>
                        <CardTitle className="text-center">ATS Score</CardTitle>
                      </CardHeader>
                      <CardContent className="text-center">
                        <div className="relative w-48 h-48 mx-auto mb-4">
                          <svg className="transform -rotate-90 w-full h-full">
                            <circle
                              cx="96"
                              cy="96"
                              r="88"
                              stroke="currentColor"
                              strokeWidth="8"
                              fill="transparent"
                              className="text-muted"
                            />
                            <motion.circle
                              cx="96"
                              cy="96"
                              r="88"
                              stroke="url(#gradient)"
                              strokeWidth="8"
                              fill="transparent"
                              strokeDasharray={`${2 * Math.PI * 88}`}
                              initial={{ strokeDashoffset: 2 * Math.PI * 88 }}
                              animate={{
                                strokeDashoffset:
                                  2 * Math.PI * 88 * (1 - atsScore / 100),
                              }}
                              transition={{ duration: 1, ease: 'easeOut' }}
                            />
                            <defs>
                              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#6366f1" />
                                <stop offset="100%" stopColor="#8b5cf6" />
                              </linearGradient>
                            </defs>
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-5xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                              {atsScore}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {atsScore >= 80
                            ? 'Excellent! Your resume is well-optimized.'
                            : atsScore >= 60
                            ? 'Good, but there is room for improvement.'
                            : 'Needs significant optimization.'}
                        </p>
                      </CardContent>
                    </Card>

                    {/* Missing Keywords */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Missing Keywords</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-2">
                          {missingKeywords.map((keyword, index) => (
                            <motion.div
                              key={keyword}
                              initial={{ opacity: 0, scale: 0 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: index * 0.1 }}
                            >
                              <Badge variant="outline" className="text-xs">
                                {keyword}
                              </Badge>
                            </motion.div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    {/* Suggestions */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">AI Suggestions</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {suggestions.map((suggestion, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-start gap-2 p-3 rounded-lg bg-muted/50"
                          >
                            <AlertCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                            <p className="text-sm">{suggestion.text}</p>
                          </motion.div>
                        ))}
                      </CardContent>
                    </Card>

                    {/* Actions */}
                    <div className="space-y-2">
                      <Button 
                        onClick={applyAllSuggestions}
                        disabled={
                          applying || 
                          !analysisResult || 
                          !resumeText.trim() ||
                          isDraftEmpty
                        }
                        className="w-full bg-gradient-to-r from-primary to-secondary"
                      >
                        {applying ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Applying...
                          </>
                        ) : (
                          <>
                            <Sparkles className="mr-2 h-4 w-4" />
                            Apply All Suggestions
                          </>
                        )}
                      </Button>
                      <Button 
                        variant="outline" 
                        className="w-full"
                        onClick={() => {
                          // Copy optimized resume text to clipboard
                          if (resumeText.trim()) {
                            navigator.clipboard.writeText(resumeText);
                            toast.success('Resume text copied to clipboard!');
                          } else {
                            toast.error('No resume text to copy');
                          }
                        }}
                      >
                        <FileText className="mr-2 h-4 w-4" />
                        Copy Resume Text
                      </Button>
                    </div>
                  </motion.div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            {!isDraftEmpty && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-8 w-full flex flex-col sm:flex-row gap-4 justify-center items-center"
              >
              {/* After optimization: Show only Preview button */}
              {optimizationApplied ? (
                <Button asChild size="lg" className="bg-gradient-to-r from-primary to-secondary">
                  <Link href={
                    resumeId 
                      ? `/builder/preview?id=${resumeId}` 
                      : guestId 
                      ? `/builder/preview?guestId=${guestId}` 
                      : '/builder/preview'
                  }>
                    Continue to Preview
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
              ) : (
                /* Before optimization: Show both Skip Optimization and Preview buttons */
                <>
                  <Button 
                    asChild 
                    size="lg" 
                    variant="outline"
                  >
                    <Link href={
                      resumeId 
                        ? `/builder/preview?id=${resumeId}` 
                        : guestId 
                        ? `/builder/preview?guestId=${guestId}` 
                        : '/builder/preview'
                    }>
                      Skip Optimization
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Link>
                  </Button>
                  
                  <Button 
                    asChild 
                    size="lg"
                    className="bg-gradient-to-r from-primary to-secondary"
                  >
                    <Link href={
                      resumeId 
                        ? `/builder/preview?id=${resumeId}` 
                        : guestId 
                        ? `/builder/preview?guestId=${guestId}` 
                        : '/builder/preview'
                    }>
                      <FileText className="mr-2 h-5 w-5" />
                      Preview Resume
                    </Link>
                  </Button>
                </>
              )}
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </PageTransition>
    </TooltipProvider>
  );
}

export default function OptimizePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <OptimizeContent />
    </Suspense>
  );
}
