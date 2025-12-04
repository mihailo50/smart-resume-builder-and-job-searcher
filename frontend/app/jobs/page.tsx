'use client';

import { useState, useEffect } from 'react';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Search,
  TrendingUp,
  FileText,
  Download,
  FileCheck,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  MapPin,
  Loader2,
  Briefcase,
  ExternalLink,
  DollarSign,
  Calendar,
  Building2,
} from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';

interface MatchResult {
  resume_id: string;
  resume_name: string;
  match_score: number;
  missing_keywords: string[];
  suggestions: string[];
  matched_keywords?: string[];
  category_matches?: {
    technical_skills?: number;
    tools?: number;
    methodologies?: number;
    soft_skills?: number;
  };
}

interface JobSearchResult {
  external_id: string;
  title: string;
  company: string;
  location: string;
  remote_type: string;
  job_type: string;
  description: string;
  requirements?: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  application_url?: string;
  company_url?: string;
  posted_date?: string;
  source: string;
  source_id: string;
  category?: string;
}

interface LocationData {
  success: boolean;
  city?: string;
  country?: string;
  country_code?: string;
  location_string?: string;
  error?: string;
  is_localhost?: boolean;
  message?: string;
}

type TabMode = 'search' | 'match';

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<TabMode>('search');
  
  // Shared state
  const [location, setLocation] = useState<string>('');
  const [locationData, setLocationData] = useState<LocationData | null>(null);
  const [detectingLocation, setDetectingLocation] = useState(false);
  
  // Job Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [jobType, setJobType] = useState<string>('');
  const [remote, setRemote] = useState(false);
  const [searching, setSearching] = useState(false);
  const [jobResults, setJobResults] = useState<JobSearchResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  
  // Job Matching state
  const [jobDescription, setJobDescription] = useState('');
  const [matching, setMatching] = useState(false);
  const [matchResults, setMatchResults] = useState<MatchResult[]>([]);
  const [matchError, setMatchError] = useState<string | null>(null);

  // Detect location on component mount
  useEffect(() => {
    detectLocation();
  }, []);

  const detectLocation = async () => {
    setDetectingLocation(true);
    try {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          async (position) => {
            const { latitude, longitude } = position.coords;
            
            try {
              const response = await api.get<LocationData>(
                `v1/jobs/detect-location/`,
                {
                  params: {
                    latitude: latitude.toString(),
                    longitude: longitude.toString(),
                  },
                }
              );
              
              if (response.success && response.location_string) {
                setLocationData(response);
                setLocation(response.location_string);
              } else {
                detectLocationFromIP();
              }
            } catch (error) {
              console.error('Geolocation reverse geocoding failed:', error);
              detectLocationFromIP();
            }
          },
          () => {
            detectLocationFromIP();
          },
          { timeout: 5000 }
        );
      } else {
        detectLocationFromIP();
      }
    } catch (error) {
      console.error('Location detection failed:', error);
      detectLocationFromIP();
    } finally {
      setDetectingLocation(false);
    }
  };

  const detectLocationFromIP = async () => {
    try {
      const response = await api.get<LocationData>('v1/jobs/detect-location/');
      
      if (response.success && response.location_string) {
        setLocationData(response);
        setLocation(response.location_string);
      }
    } catch (error) {
      console.error('IP-based location detection failed:', error);
    }
  };

  const handleJobSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchError('Please enter a job search query');
      return;
    }

    setSearching(true);
    setSearchError(null);
    setJobResults([]);

    try {
      const response = await api.post<{
        success: boolean;
        results: JobSearchResult[];
        count: number;
        total_results?: number;
        page?: number;
        total_pages?: number;
        source?: string;
      }>('v1/jobs/search/', {
        query: searchQuery,
        location: location || undefined,
        country: locationData?.country_code || 'US',
        job_type: jobType && jobType.trim() ? jobType : undefined,
        remote: remote,
        max_results: 20,
        page: currentPage,
      });

      if (response.success && response.results) {
        setJobResults(response.results);
        setTotalResults(response.total_results || response.count);
        setCurrentPage(response.page || 1);
      } else {
        setSearchError('No jobs found. Try adjusting your search criteria.');
      }
    } catch (err: any) {
      console.error('Job search error:', err);
      
      let errorMessage = 'Failed to search jobs. Please try again later.';
      
      if (err.response) {
        const backendError = err.response;
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
      } else if (err.message && !err.message.includes('HTTP error!')) {
        errorMessage = err.message;
      }
      
      setSearchError(errorMessage);
    } finally {
      setSearching(false);
    }
  };

  const handleFindMatches = async () => {
    if (!jobDescription.trim()) {
      setMatchError('Please enter a job description');
      return;
    }

    setMatching(true);
    setMatchError(null);
    setMatchResults([]);

    try {
      const response = await api.post<{
        results: MatchResult[];
        count: number;
        message?: string;
      }>('v1/jobs/match-all/', {
        job_description: jobDescription,
        location: location || undefined,
      });

      if (response.results && response.results.length > 0) {
        setMatchResults(response.results);
      } else {
        setMatchError(
          response.message ||
            'No resumes found. Please create a resume first to match against job descriptions.'
        );
      }
    } catch (err: any) {
      console.error('Job matching error:', err);
      
      let errorMessage = 'Failed to match resumes. Please try again later.';
      
      if (err.response) {
        const backendError = err.response;
        
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
      } else if (err.message && !err.message.includes('HTTP error!')) {
        errorMessage = err.message;
      }
      
      setMatchError(errorMessage);
    } finally {
    setMatching(false);
    }
  };

  const formatSalary = (min?: number, max?: number, currency = 'USD') => {
    if (!min && !max) return 'Salary not specified';
    const symbol = currency === 'USD' ? '$' : currency;
    if (min && max) {
      return `${symbol}${min.toLocaleString()} - ${symbol}${max.toLocaleString()}`;
    }
    return min ? `${symbol}${min.toLocaleString()}+` : `Up to ${symbol}${max?.toLocaleString()}`;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Date not specified';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-6xl mx-auto"
          >
            <div className="text-center mb-8">
              <h1 className="text-4xl md:text-5xl font-bold mb-4">
                Jobs
              </h1>
              <p className="text-xl text-muted-foreground">
                Search for jobs or match your resumes against job descriptions
              </p>
            </div>

            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabMode)} className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-8">
                <TabsTrigger value="search" className="text-base">
                  <Search className="mr-2 h-4 w-4" />
                  Search Jobs
                </TabsTrigger>
                <TabsTrigger value="match" className="text-base">
                  <TrendingUp className="mr-2 h-4 w-4" />
                  Match Resumes
                </TabsTrigger>
              </TabsList>

              <TabsContent value="search" className="space-y-6">
                <Card className="mb-6">
              <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="flex items-center gap-2 mb-2">
                  <Search className="h-5 w-5 text-primary" />
                          Search Job Postings
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">
                          Find job opportunities from top job boards. No resume required.
                        </p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Search Query */}
                      <div>
                        <Label htmlFor="search-query">Job Title or Keywords</Label>
                        <Input
                          id="search-query"
                          placeholder="e.g., Software Engineer, Data Scientist, Product Manager"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && searchQuery.trim()) {
                              handleJobSearch();
                            }
                          }}
                        />
                      </div>

                      {/* Location Input */}
                      <div>
                        <Label htmlFor="search-location" className="flex items-center gap-2 mb-2">
                          <MapPin className="h-4 w-4" />
                          Location (optional)
                        </Label>
                        <div className="flex gap-2">
                          <Input
                            id="search-location"
                            placeholder="e.g., New York, NY or Remote"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            className="flex-1"
                          />
                          {detectingLocation && (
                            <Loader2 className="h-4 w-4 animate-spin self-center" />
                          )}
                          {!detectingLocation && !location && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={detectLocation}
                              type="button"
                            >
                              Auto-detect
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* Filters */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="job-type">Job Type</Label>
                          <Select value={jobType || undefined} onValueChange={(value) => setJobType(value || '')}>
                            <SelectTrigger id="job-type">
                              <SelectValue placeholder="All types" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="full-time">Full-time</SelectItem>
                              <SelectItem value="part-time">Part-time</SelectItem>
                              <SelectItem value="contract">Contract</SelectItem>
                              <SelectItem value="internship">Internship</SelectItem>
                              <SelectItem value="freelance">Freelance</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="flex items-end">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={remote}
                              onChange={(e) => setRemote(e.target.checked)}
                              className="w-4 h-4"
                            />
                            <span className="text-sm">Remote only</span>
                          </label>
                        </div>
                      </div>

                      {/* Error Message */}
                      {searchError && (
                        <div className="bg-destructive/10 text-destructive p-3 rounded-lg flex items-center gap-2">
                          <AlertCircle className="h-4 w-4" />
                          <span className="text-sm">{searchError}</span>
                        </div>
                      )}

                      {/* Search Button */}
                      <Button
                        onClick={handleJobSearch}
                        disabled={!searchQuery.trim() || searching}
                        className="w-full bg-gradient-to-r from-primary to-secondary"
                      >
                        {searching ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Searching...
                          </>
                        ) : (
                          <>
                            <Search className="mr-2 h-4 w-4" />
                            Search Jobs
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Job Search Results */}
                <AnimatePresence>
                  {searching && (
                    <div className="space-y-4">
                      {[1, 2, 3].map((i) => (
                        <Card key={i}>
                          <CardContent className="p-6">
                            <Skeleton className="h-8 w-64 mb-4" />
                            <Skeleton className="h-4 w-full mb-2" />
                            <Skeleton className="h-4 w-3/4" />
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}

                  {jobResults.length > 0 && !searching && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="space-y-6"
                    >
                      <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold">Job Results</h2>
                        <Badge variant="outline" className="text-sm">
                          {totalResults} job{totalResults !== 1 ? 's' : ''} found
                        </Badge>
                      </div>

                      {jobResults.map((job, index) => (
                        <motion.div
                          key={job.external_id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          whileHover={{ scale: 1.01 }}
                        >
                          <Card className="border-2 hover:border-primary/50 transition-colors">
                            <CardHeader>
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <CardTitle className="text-xl mb-2">{job.title}</CardTitle>
                                  <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                                    <div className="flex items-center gap-1">
                                      <Building2 className="h-4 w-4" />
                                      {job.company}
                                    </div>
                                    <div className="flex items-center gap-1">
                                      <MapPin className="h-4 w-4" />
                                      {job.location}
                                    </div>
                                    {job.salary_min || job.salary_max ? (
                                      <div className="flex items-center gap-1">
                                        <DollarSign className="h-4 w-4" />
                                        {formatSalary(job.salary_min, job.salary_max, job.currency)}
                                      </div>
                                    ) : null}
                                    {job.posted_date && (
                                      <div className="flex items-center gap-1">
                                        <Calendar className="h-4 w-4" />
                                        {formatDate(job.posted_date)}
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <div className="flex flex-col gap-2 ml-4">
                                  <Badge variant="outline" className="w-fit">
                                    {job.job_type}
                                  </Badge>
                                  {job.remote_type !== 'onsite' && (
                                    <Badge variant="secondary" className="w-fit">
                                      {job.remote_type}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </CardHeader>
                            <CardContent>
                              <p className="text-sm text-muted-foreground mb-4 line-clamp-3">
                                {job.description}
                              </p>
                              {job.requirements && (
                                <div className="mb-4">
                                  <p className="text-sm font-semibold mb-2">Requirements:</p>
                                  <p className="text-sm text-muted-foreground line-clamp-2">
                                    {job.requirements}
                                  </p>
                                </div>
                              )}
                              <div className="flex gap-2">
                                {job.application_url && (
                                  <Button asChild className="flex-1">
                                    <a
                                      href={job.application_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      Apply Now
                                      <ExternalLink className="ml-2 h-4 w-4" />
                                    </a>
                                  </Button>
                                )}
                                <Button
                                  variant="outline"
                                  onClick={() => {
                                    setActiveTab('match');
                                    setJobDescription(`Title: ${job.title}\n\nCompany: ${job.company}\n\nDescription: ${job.description}\n\nRequirements: ${job.requirements || 'N/A'}`);
                                  }}
                                >
                                  <TrendingUp className="mr-2 h-4 w-4" />
                                  Match Resume
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>

                {jobResults.length === 0 && !searching && !searchError && (
                  <div className="text-center text-muted-foreground py-12">
                    <Briefcase className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">
                      Enter a job title or keywords to search for job opportunities.
                    </p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="match" className="space-y-6">
                <Card className="mb-6">
                  <CardHeader>
                    <div>
                      <CardTitle className="flex items-center gap-2 mb-2">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        Match Your Resumes
                </CardTitle>
                      <p className="text-sm text-muted-foreground">
                        See how well your resumes match a specific job description. Requires at least one resume.
                      </p>
                    </div>
              </CardHeader>
              <CardContent>
                    <div className="space-y-4">
                      {/* Location Input */}
                      <div>
                        <Label htmlFor="match-location" className="flex items-center gap-2 mb-2">
                          <MapPin className="h-4 w-4" />
                          Location (optional)
                        </Label>
                        <div className="flex gap-2">
                          <Input
                            id="match-location"
                            placeholder="e.g., New York, NY or Remote"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            className="flex-1"
                          />
                          {detectingLocation && (
                            <Loader2 className="h-4 w-4 animate-spin self-center" />
                          )}
                          {!detectingLocation && !location && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={detectLocation}
                              type="button"
                            >
                              Auto-detect
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* Job Description Input */}
                      <div>
                        <Label htmlFor="job-description">Job Description</Label>
                <Textarea
                          id="job-description"
                  placeholder="Paste the job description here..."
                  className="min-h-[200px] mb-4"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                />
                        <p className="text-xs text-muted-foreground">
                          Minimum 30 characters. Include job title, responsibilities, requirements, and qualifications for best results.
                        </p>
                      </div>

                      {/* Error Message */}
                      {matchError && (
                        <div className="bg-destructive/10 text-destructive p-3 rounded-lg flex items-center gap-2">
                          <AlertCircle className="h-4 w-4" />
                          <span className="text-sm">{matchError}</span>
                        </div>
                      )}

                      {/* Submit Button */}
                <Button
                  onClick={handleFindMatches}
                  disabled={!jobDescription.trim() || matching}
                  className="w-full bg-gradient-to-r from-primary to-secondary"
                >
                  {matching ? (
                    <>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        className="mr-2"
                      >
                        <Sparkles className="h-4 w-4" />
                      </motion.div>
                      Finding Matches...
                    </>
                  ) : (
                    <>
                      Find Matches
                      <TrendingUp className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
                    </div>
              </CardContent>
            </Card>

            {/* Loading Skeleton */}
            {matching && (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-6">
                      <Skeleton className="h-8 w-64 mb-4" />
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-3/4" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

                {/* Match Results */}
            <AnimatePresence>
                  {matchResults.length > 0 && !matching && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold">Match Results</h2>
                    <Badge variant="outline" className="text-sm">
                          {matchResults.length} Resume{matchResults.length !== 1 ? 's' : ''} Found
                    </Badge>
                  </div>

                      {matchResults.map((result, index) => (
                    <motion.div
                          key={result.resume_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ scale: 1.02 }}
                    >
                      <Card className="border-2 hover:border-primary/50 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                              <FileText className="h-6 w-6 text-primary" />
                              <div>
                                    <CardTitle className="text-xl">
                                      {result.resume_name}
                                    </CardTitle>
                                <p className="text-sm text-muted-foreground mt-1">
                                  Match Score
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                                    {result.match_score}%
                              </div>
                              <Progress
                                    value={result.match_score}
                                className="w-32 h-2 mt-2"
                              />
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                              {result.missing_keywords &&
                                result.missing_keywords.length > 0 && (
                            <div>
                              <div className="flex items-center gap-2 mb-2">
                                <AlertCircle className="h-4 w-4 text-primary" />
                                      <span className="text-sm font-semibold">
                                        Missing Keywords
                                      </span>
                              </div>
                              <div className="flex flex-wrap gap-2">
                                      {result.missing_keywords.map(
                                        (keyword, idx) => (
                                  <Badge
                                    key={idx}
                                    variant="outline"
                                    className="text-xs bg-destructive/10 text-destructive border-destructive/20"
                                  >
                                    {keyword}
                                  </Badge>
                                        )
                                      )}
                                    </div>
                                  </div>
                                )}

                              {result.matched_keywords &&
                                result.matched_keywords.length > 0 && (
                                  <div>
                                    <div className="flex items-center gap-2 mb-2">
                                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                                      <span className="text-sm font-semibold">
                                        Matched Keywords
                                      </span>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                      {result.matched_keywords
                                        .slice(0, 10)
                                        .map((keyword, idx) => (
                                          <Badge
                                            key={idx}
                                            variant="outline"
                                            className="text-xs bg-green-500/10 text-green-600 border-green-500/20"
                                          >
                                            {keyword}
                                          </Badge>
                                ))}
                              </div>
                            </div>
                          )}

                              {result.suggestions &&
                                result.suggestions.length > 0 && (
                            <div>
                              <div className="flex items-center gap-2 mb-2">
                                <CheckCircle2 className="h-4 w-4 text-primary" />
                                      <span className="text-sm font-semibold">
                                        AI Suggestions
                                      </span>
                              </div>
                              <ul className="space-y-2">
                                {result.suggestions.map((suggestion, idx) => (
                                        <li
                                          key={idx}
                                          className="text-sm text-muted-foreground flex items-start gap-2"
                                        >
                                    <span className="text-primary mt-1">•</span>
                                    <span>{suggestion}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          <div className="flex gap-2 pt-4">
                                <Button
                                  asChild
                                  variant="outline"
                                  className="flex-1"
                                >
                                  <Link
                                    href={`/builder/preview?id=${result.resume_id}`}
                                  >
                                    <FileText className="mr-2 h-4 w-4" />
                                    View Resume
                                  </Link>
                                </Button>
                            <Button
                              asChild
                              variant="outline"
                              className="flex-1"
                            >
                              <Link href="/cover-letter">
                                <Sparkles className="mr-2 h-4 w-4" />
                                Generate Cover Letter
                              </Link>
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>

                {matchResults.length === 0 && !matching && !matchError && (
              <div className="text-center text-muted-foreground py-12">
                <FileCheck className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">
                      Paste a job description and click &quot;Find Matches&quot; to
                      see how your resumes compare.
                </p>
              </div>
            )}
              </TabsContent>
            </Tabs>
          </motion.div>
        </div>
      </div>
    </PageTransition>
  );
}
