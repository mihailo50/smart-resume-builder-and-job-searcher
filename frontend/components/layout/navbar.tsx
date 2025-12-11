'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useTheme } from 'next-themes';
import { motion } from 'framer-motion';
import {
  Sun,
  Moon,
  Menu,
  X,
  Github,
  Sparkles,
  LogOut,
  User,
  Save,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { usePathname } from 'next/navigation';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { isAuthenticated as checkIsAuthenticated, hasGuestResumeData, getGuestEmail, getGuestResumeId } from '@/lib/guest-resume';
import { SignupModal } from '@/components/resume/signup-modal';
import { useGlobalDirtyState } from '@/lib/use-dirty-guard';

const navLinks = [
  { name: 'Home', href: '/' },
  { name: 'Builder', href: '/builder' },
  { name: 'Jobs', href: '/jobs' },
  { name: 'Templates', href: '/templates' },
  { name: 'Pricing', href: '/pricing' },
];

export function Navbar() {
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [hasGuestData, setHasGuestData] = useState(false);
  const [guestEmail, setGuestEmail] = useState<string | null>(null);
  const { theme, setTheme } = useTheme();
  const pathname = usePathname();
  const { isDirty: isFormDirty } = useGlobalDirtyState();

  // Check for meaningful guest resume progress
  const checkGuestProgress = (): boolean => {
    if (typeof window === 'undefined') return false;
    
    try {
      const guestDataStr = localStorage.getItem('guest_resume_data');
      if (!guestDataStr) return false;
      
      const data = JSON.parse(guestDataStr);
      
      // Check for meaningful personal info
      if (data.personal) {
        if (
          data.personal.fullName?.trim() ||
          data.personal.email?.trim() ||
          data.personal.phone?.trim() ||
          data.personal.professionalTagline?.trim() ||
          data.personal.summary?.trim()
        ) {
          return true;
        }
      }
      
      // Check for meaningful experiences
      if (data.experiences && Array.isArray(data.experiences) && data.experiences.length > 0) {
        const hasValidExperience = data.experiences.some(
          (exp: any) => exp.company?.trim() && exp.position?.trim()
        );
        if (hasValidExperience) return true;
      }
      
      // Check for meaningful projects
      if (data.projects && Array.isArray(data.projects) && data.projects.length > 0) {
        const hasValidProject = data.projects.some(
          (proj: any) => proj.title?.trim()
        );
        if (hasValidProject) return true;
      }
      
      // Check for meaningful education
      if (data.educations && Array.isArray(data.educations) && data.educations.length > 0) {
        const hasValidEducation = data.educations.some(
          (edu: any) => edu.institution?.trim() && edu.degree?.trim()
        );
        if (hasValidEducation) return true;
      }
      
      // Check for meaningful certifications
      if (data.certifications && Array.isArray(data.certifications) && data.certifications.length > 0) {
        const hasValidCert = data.certifications.some(
          (cert: any) => cert.title?.trim()
        );
        if (hasValidCert) return true;
      }
      
      // Check for meaningful skills
      if (data.skills && Array.isArray(data.skills) && data.skills.length > 0) {
        const hasValidSkill = data.skills.some(
          (skill: any) => skill.name?.trim()
        );
        if (hasValidSkill) return true;
      }
      
      // Check for meaningful languages
      if (data.languages && Array.isArray(data.languages) && data.languages.length > 0) {
        const hasValidLanguage = data.languages.some(
          (lang: any) => lang.name?.trim()
        );
        if (hasValidLanguage) return true;
      }
      
      // Check for meaningful interests
      if (data.interests && Array.isArray(data.interests) && data.interests.length > 0) {
        const hasValidInterest = data.interests.some(
          (interest: any) => interest.name?.trim()
        );
        if (hasValidInterest) return true;
      }
      
      // Check for optimized summary or text
      if (data.optimizedSummary?.trim() || data.optimizedText?.trim()) {
        return true;
      }
      
      return false;
    } catch (error) {
      // If parsing fails or localStorage is corrupted, hide button
      console.error('Failed to check guest progress:', error);
      return false;
    }
  };

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('auth_token');
    const userStr = localStorage.getItem('user');
    if (token && userStr) {
      setIsAuthenticated(true);
      try {
        setUser(JSON.parse(userStr));
      } catch {
        setUser(null);
      }
      // Optionally fetch current user info from API
      // loadUserInfo();
    } else {
      setIsAuthenticated(false);
      // Check for meaningful guest data
      setHasGuestData(checkGuestProgress());
      setGuestEmail(getGuestEmail());
    }
  }, []);

  // Periodically check for guest data changes
  useEffect(() => {
    if (isAuthenticated) return;
    
    const interval = setInterval(() => {
      const hasProgress = checkGuestProgress();
      setHasGuestData(hasProgress);
      setGuestEmail(getGuestEmail());
    }, 2000);

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const loadUserInfo = async () => {
    try {
      const response = await api.get<any>('/v1/auth/me/');
      if (response.user) {
        setUser(response.user);
        localStorage.setItem('user', JSON.stringify(response.user));
      }
    } catch (error) {
      // If failed, use stored user info
      console.error('Failed to load user info:', error);
    }
  };

  const handleLogout = async () => {
    try {
      // Call logout endpoint
      await api.post('/v1/auth/logout/');
      
      // Clear local storage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      setIsAuthenticated(false);
      setUser(null);
      
      toast.success('Logged out successfully');
      router.push('/');
    } catch (error: any) {
      console.error('Logout failed:', error);
      // Still clear local storage even if API call fails
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setIsAuthenticated(false);
      setUser(null);
      router.push('/');
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              <Sparkles className="h-6 w-6 text-primary" />
            </motion.div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              ResumeAI Pro
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'text-sm font-medium transition-colors hover:text-primary',
                  pathname === link.href
                    ? 'text-primary'
                    : 'text-muted-foreground'
                )}
              >
                {link.name}
              </Link>
            ))}
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center space-x-4">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="relative"
            >
              <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>

            {/* GitHub Star */}
            <Button
              variant="ghost"
              size="icon"
              asChild
              className="hidden sm:flex"
            >
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github className="h-5 w-5" />
                <span className="sr-only">GitHub</span>
              </a>
            </Button>

            {/* User Menu / CTA Button */}
            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="hidden md:flex">
                    <User className="mr-2 h-4 w-4" />
                    {user?.email?.split('@')[0] || 'Account'}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>
                    {user?.email || 'Account'}
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/dashboard">
                      Dashboard
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/builder">
                      Resume Builder
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <>
                {/* Save Progress button for guests (only show if meaningful progress exists) */}
                {hasGuestData && (
                  <Button
                    variant={isFormDirty ? "default" : "outline"}
                    size="sm"
                    onClick={() => setShowSaveModal(true)}
                    className="hidden md:flex flex-col items-start gap-0 leading-tight"
                  >
                    <span className="flex items-center text-sm font-semibold">
                      <Save className="mr-2 h-4 w-4" />
                      {isFormDirty ? 'Save Progress' : 'Save & Continue Later'}
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      {isFormDirty 
                        ? 'Unsaved changes - sign up to save permanently'
                        : 'Create free account to save your progress permanently'}
                    </span>
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  asChild
                  className="hidden md:flex"
                >
                  <Link href="/login">Sign In</Link>
                </Button>
                <Button
                  asChild
                  className="hidden md:flex bg-gradient-to-r from-primary to-secondary hover:opacity-90"
                >
                  <Link href="/builder">Start Building</Link>
                </Button>
              </>
            )}

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden py-4 space-y-2"
          >
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  'block px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  pathname === link.href
                    ? 'text-primary bg-primary/10'
                    : 'text-muted-foreground hover:bg-accent'
                )}
              >
                {link.name}
              </Link>
            ))}
            <div className="px-4 pt-2 space-y-2">
              {isAuthenticated ? (
                <>
                  <Button
                    variant="outline"
                    asChild
                    className="w-full"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Link href="/dashboard">Dashboard</Link>
                  </Button>
                  <Button
                    onClick={() => {
                      handleLogout();
                      setMobileMenuOpen(false);
                    }}
                    variant="destructive"
                    className="w-full"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  {/* Save Progress button for guests (only show if meaningful progress exists) */}
                  {hasGuestData && (
                    <Button
                      variant={isFormDirty ? "default" : "outline"}
                      onClick={() => {
                        setShowSaveModal(true);
                        setMobileMenuOpen(false);
                      }}
                      className="w-full flex-col items-start gap-0 leading-tight"
                    >
                      <span className="flex items-center text-sm font-semibold">
                        <Save className="mr-2 h-4 w-4" />
                        {isFormDirty ? 'Save Progress' : 'Save & Continue Later'}
                      </span>
                      <span className="text-[11px] text-muted-foreground">
                        {isFormDirty 
                          ? 'Unsaved changes - sign up to save permanently'
                          : 'Create free account to save your progress permanently'}
                      </span>
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    asChild
                    className="w-full"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Link href="/login">Sign In</Link>
                  </Button>
                  <Button
                    asChild
                    className="w-full bg-gradient-to-r from-primary to-secondary"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Link href="/builder">Start Building</Link>
                  </Button>
                </>
              )}
            </div>
          </motion.div>
        )}
      </div>
      
      {/* Save Modal for Guests */}
      {!isAuthenticated && (
        <SignupModal
          open={showSaveModal}
          onOpenChange={setShowSaveModal}
          prefillEmail={guestEmail || undefined}
          onSignupSuccess={(resumeId) => {
            setShowSaveModal(false);
            setIsAuthenticated(true);
            toast.success('Resume saved! Preparing download...');
            setTimeout(() => {
              router.push(`/builder/preview?id=${resumeId}&openExport=true`);
            }, 1000);
          }}
          guestResumeId={hasGuestData ? getGuestResumeId() : undefined}
        />
      )}
    </nav>
  );
}


