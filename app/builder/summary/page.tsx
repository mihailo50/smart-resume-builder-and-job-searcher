'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { useGuestGuard } from '@/lib/use-guest-guard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ArrowRight, ArrowLeft, Sparkles, Loader2, Info } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { 
  isAuthenticated, 
  saveGuestResume, 
  loadGuestResume, 
  getGuestResumeId,
} from '@/lib/guest-resume';
import { AISummaryModal } from '@/components/resume/ai-summary-modal';

export default function SummaryPage() {
  // Enable guest guard to prevent data loss
  useGuestGuard();
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('id') || searchParams.get('resumeId');
  const guestId = searchParams.get('guestId');
  const [professionalTagline, setProfessionalTagline] = useState('');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [progress, setProgress] = useState(82); // Step 9 of 11
  const [showAIModal, setShowAIModal] = useState(false);
  const [enhancedSummary, setEnhancedSummary] = useState<string | null>(null);
  const [generatingAI, setGeneratingAI] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [isAIEnhanced, setIsAIEnhanced] = useState(false);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    
    if (guestId || (!resumeId && !isAuthenticated())) {
      // Guest mode - load from localStorage
      loadGuestSummary();
    } else if (resumeId && isAuthenticated()) {
      // Authenticated mode - load from API
      loadSummary();
    }
  }, [resumeId, guestId]);

  const loadSummary = async () => {
    if (!resumeId) return;
    
    try {
      setLoading(true);
      const resume = await api.get<{
        professional_tagline?: string;
        summary?: string;
        optimized_summary?: string;
      }>(`/v1/resumes/${resumeId}/`);
      setProfessionalTagline(resume.professional_tagline || resume.summary || '');
      const loadedSummary = resume.optimized_summary || '';
      setSummary(loadedSummary);
      // If there's an optimized_summary, it's likely AI-enhanced
      setIsAIEnhanced(!!resume.optimized_summary);
    } catch (error: any) {
      console.error('Failed to load summary:', error);
      toast.error('Failed to load summary');
    } finally {
      setLoading(false);
    }
  };

  const loadGuestSummary = () => {
    try {
      const guestData = loadGuestResume();
      const tagline = guestData.personal?.professionalTagline || guestData.personal?.summary || '';
      const optimized = guestData.optimizedSummary || '';
      setProfessionalTagline(tagline);
      setSummary(optimized);
      // If there's an optimized summary, it's likely AI-enhanced
      setIsAIEnhanced(!!optimized);
    } catch (error) {
      console.error('Failed to load guest summary:', error);
    }
  };

  const handleGenerateAI = async () => {
      // Check if there's a summary to enhance
      if (!summary.trim()) {
        toast.error('Please enter a summary first before generating with AI.');
        return;
      }

    setGeneratingAI(true);
    setAiError(null);
    setShowAIModal(true);

    try {
      // Prepare resume data for context (optional, but helpful)
      let resumeDataForContext: any = null;
      
      if (guestId) {
        // Guest mode - get data from localStorage
        const guestData = loadGuestResume();
        resumeDataForContext = {
          full_name: guestData.personal?.fullName,
          experiences: guestData.experiences || [],
          educations: guestData.educations || [],
          skills: guestData.skills || [],
        };
      } else if (resumeId && isAuthenticated()) {
        // Authenticated mode - get from API (optional, can work without it)
        try {
          const resume = await api.get<{
            full_name?: string;
            experiences?: any[];
            educations?: any[];
            skills?: any[];
          }>(`/v1/resumes/${resumeId}/`);
          resumeDataForContext = {
            full_name: resume.full_name,
            experiences: resume.experiences || [],
            educations: resume.educations || [],
            skills: resume.skills || [],
          };
        } catch (error) {
          // Continue without resume data if API fails
          console.warn('Could not load resume data for context:', error);
        }
      }

      // Call enhance-summary endpoint
      const response = await api.post<{
        enhanced_summary: string;
        tone: string;
      }>('v1/ai/enhance-summary/', {
        summary_text: summary,
        resume_data: resumeDataForContext,
        tone: 'professional',
      });

      if (response.enhanced_summary) {
        setEnhancedSummary(response.enhanced_summary);
        
        // Mark AI generation as used for guests
      } else {
        throw new Error('No enhanced summary received');
      }
    } catch (error: any) {
      console.error('AI summary generation failed:', error);
      
      if (error?.response?.detail) {
        const detailMessage = error.response.detail;
        setAiError(detailMessage);
        toast.error(detailMessage);
        return;
      }
      
      let errorMessage = 'Failed to generate enhanced summary. Please try again.';
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
      
      setAiError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setGeneratingAI(false);
    }
  };

  const handleAcceptEnhancedSummary = (enhanced: string) => {
    setSummary(enhanced);
    setIsAIEnhanced(true);
    toast.success('Enhanced summary applied!');
  };

  const handleNext = async (e?: React.MouseEvent) => {
    console.log('========================================');
    console.log('🚀🚀🚀 handleNext FUNCTION CALLED 🚀🚀🚀');
    console.log('========================================');
    console.log('Event:', e);
    console.log('State:', { 
      resumeId, 
      guestId, 
      isAuthenticated: isAuthenticated(),
      saving,
      loading,
      professionalTagline: professionalTagline?.substring(0, 50),
      summary: summary?.substring(0, 50)
    });
    
    // Prevent any default behavior
    if (e) {
      e.preventDefault();
      e.stopPropagation();
      console.log('✅ Prevented default and stopped propagation');
    }
    
    // Don't proceed if already saving or if no resume/guest ID
    if (saving || loading) {
      console.warn('⚠️ Already saving/loading, ignoring click');
      return;
    }
    
    if (!resumeId && !guestId) {
      console.error('❌ No resumeId or guestId!');
      toast.error('Resume ID is missing');
      return;
    }
    
    console.log('✅ Pre-checks passed, setting saving=true');
    setSaving(true);
    
    try {
      // Check if user is authenticated
      if (isAuthenticated() && resumeId) {
        console.log('📡 Authenticated flow - saving to API');
        console.log('Making request: PUT /v1/resumes/' + resumeId + '/optimized-summary/');
        console.log('Payload:', { optimized_summary: summary || '' });
        
        // Authenticated flow - save to API (unified: save summary to optimized_summary)
        await api.put(`/v1/resumes/${resumeId}/optimized-summary/`, {
          optimized_summary: summary || '',
        });
        
        // Also save professional tagline if provided (for backwards compatibility)
        if (professionalTagline && professionalTagline.trim()) {
          await api.put(`/v1/resumes/${resumeId}/summary/`, {
            professional_tagline: professionalTagline,
            summary: professionalTagline,  // For backwards compat
          });
        }
        
        console.log('✅✅✅ ALL API CALLS SUCCESSFUL ✅✅✅');
        toast.success('Summary saved');
      } else {
        console.log('💾 Guest flow - saving to localStorage');
        // Guest flow - save to localStorage
        const guestData = loadGuestResume();
        saveGuestResume({
          personal: {
            ...guestData.personal,
            professionalTagline: professionalTagline || '',
            summary: professionalTagline || '',  // Keep for backwards compat
          },
          optimizedSummary: summary || '',  // Primary field
        });
        console.log('✅ Guest data saved to localStorage');
        toast.success('Summary saved');
      }
    } catch (error: any) {
      console.error('❌❌❌ ERROR SAVING SUMMARY ❌❌❌');
      console.error('Error object:', error);
      console.error('Error message:', error?.message);
      console.error('Error stack:', error?.stack);
      toast.error(error?.message || 'Failed to save summary');
      // Continue with navigation even if save fails
    }
    
    // ALWAYS navigate, even if there was an error
    const targetUrl = isAuthenticated() && resumeId 
      ? `/builder/optimize?id=${resumeId}`
      : `/builder/optimize?guestId=${guestId || getGuestResumeId()}`;
    
    console.log('========================================');
    console.log('🧭🧭🧭 NAVIGATION TIME 🧭🧭🧭');
    console.log('========================================');
    console.log('Target URL:', targetUrl);
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    console.log('Is authenticated:', isAuthenticated());
    console.log('Resume ID:', resumeId);
    console.log('Guest ID:', guestId);
    
    // Set saving to false before navigation
    setSaving(false);
    console.log('✅ Set saving=false');
    
    // Try router.push first
    console.log('Attempting router.push...');
    try {
      router.push(targetUrl);
      console.log('✅ router.push called');
    } catch (e) {
      console.error('❌ router.push threw error:', e);
      console.log('🔄 Falling back to window.location.href');
      window.location.href = targetUrl;
    }
    
    // ALWAYS use window.location as final fallback - this MUST work
    console.log('🔄 ALSO setting window.location.href as backup');
    setTimeout(() => {
      console.log('⏰ Timeout fired - forcing navigation with window.location.href');
      if (window.location.href !== targetUrl) {
        console.log('🔄 Current URL does not match target, forcing navigation');
        window.location.href = targetUrl;
      } else {
        console.log('✅ URL already matches target');
      }
    }, 50);
    
    console.log('========================================');
    console.log('✅ handleNext FUNCTION COMPLETED');
    console.log('========================================');
  };

  return (
    <TooltipProvider>
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">Step 9 of 11</span>
                <span className="text-sm font-medium text-muted-foreground">{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Professional Summary
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        aria-label="Summary vs Optimization"
                        className="text-muted-foreground hover:text-primary transition-colors"
                      >
                        <Info className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Summary = 3–5 sentence professional profile. Optimization = full resume rewrite with job keywords.</p>
                    </TooltipContent>
                  </Tooltip>
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-2">
                  Use this step to polish the short paragraph that introduces you at the top of your resume. Stage 6 will handle full-resume optimization for a specific role.
                </p>
              </CardHeader>
              <CardContent>
              <div className="space-y-6">
                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      <span className="ml-3 text-muted-foreground">Loading summary...</span>
                    </div>
                  ) : (
                    <>
                      <div className="space-y-2">
                        <Label>
                          Professional Tagline <span className="text-muted-foreground">(optional, max 300 characters)</span>
                        </Label>
                        <Textarea
                          placeholder="e.g., Senior Full-Stack Engineer specializing in scalable SaaS platforms"
                          rows={3}
                          maxLength={300}
                          value={professionalTagline}
                          onChange={(e) => setProfessionalTagline(e.target.value)}
                        />
                        <p className="text-xs text-muted-foreground">
                          {professionalTagline.length}/300 characters
                        </p>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Label className="flex-1">Professional Summary</Label>
                          {summary && isAIEnhanced && (
                            <Badge variant="secondary">
                              AI-Enhanced Summary (full length)
                            </Badge>
                          )}
                        </div>
                        <Textarea
                          placeholder="Write or paste your full professional summary. This can be as long as needed—perfect for AI-enhanced versions."
                          rows={10}
                          value={summary}
                          onChange={(e) => setSummary(e.target.value)}
                          className="min-h-[200px]"
                        />
                        <p className="text-xs text-muted-foreground">
                          No character limit. This is the full summary that will appear in your resume preview and exports.
                        </p>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/50 border border-primary/20">
                        <p className="text-sm text-muted-foreground mb-2">
                          <strong>Tip:</strong> Keep your summary concise and focused on your most
                          relevant experience and achievements. Use this section to stand out!
                        </p>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="text-primary"
                          onClick={handleGenerateAI}
                          disabled={generatingAI || (!summary.trim() && !resumeId && !guestId)}
                        >
                          {generatingAI ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Generating...
                            </>
                          ) : (
                            <>
                              <Sparkles className="mr-2 h-4 w-4" />
                              Enhance this summary with AI
                            </>
                          )}
                        </Button>
                      </div>

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
                        <div className="flex gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            asChild
                          >
                            <Link href={
                              resumeId 
                                ? `/builder/preview?id=${resumeId}` 
                                : guestId 
                                ? `/builder/preview?guestId=${guestId}` 
                                : '/builder/preview'
                            }>
                              Skip to Preview
                            </Link>
                          </Button>
                          <Button
                            type="button"
                            onClick={(e) => {
                              console.log('Button clicked!', { saving, loading, resumeId, guestId });
                              handleNext(e);
                            }}
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
                                Next: AI Optimize
                                <ArrowRight className="ml-2 h-4 w-4" />
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* AI Summary Modal */}
        <AISummaryModal
          open={showAIModal}
          onOpenChange={setShowAIModal}
          originalSummary={summary}
          enhancedSummary={enhancedSummary || undefined}
          onAccept={handleAcceptEnhancedSummary}
          isGenerating={generatingAI}
          error={aiError || undefined}
        />
      </div>
    </PageTransition>
    </TooltipProvider>
  );
}


