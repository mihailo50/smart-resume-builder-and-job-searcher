const GUEST_RESUME_KEY = 'guest_resume_data';
const GUEST_RESUME_ID_KEY = 'guest_resume_id';
const GUEST_EMAIL_KEY = 'guest_email';

export interface GuestResumeData {
  personal?: {
    fullName?: string;
    email?: string;
    phone?: string;
    location?: string;
    linkedin?: string;
    github?: string;
    portfolio?: string;
  };
  summary?: {
    summary?: string;
    professionalTagline?: string;
  };
  experiences?: Array<{
    title?: string;
    company?: string;
    location?: string;
    startDate?: string;
    endDate?: string;
    current?: boolean;
    description?: string;
    order?: number;
  }>;
  educations?: Array<{
    degree?: string;
    school?: string;
    location?: string;
    startDate?: string;
    endDate?: string;
    current?: boolean;
    description?: string;
    order?: number;
  }>;
  skills?: Array<{
    name?: string;
    level?: string;
    order?: number;
  }>;
  projects?: Array<{
    title?: string;
    description?: string;
    technologies?: string;
    startDate?: string;
    endDate?: string;
    order?: number;
  }>;
  certifications?: Array<{
    name?: string;
    issuer?: string;
    issueDate?: string;
    expiryDate?: string;
    order?: number;
  }>;
  languages?: Array<{
    name?: string;
    proficiency?: string;
    order?: number;
  }>;
  interests?: Array<{
    name?: string;
    order?: number;
  }>;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  const token = localStorage.getItem('auth_token');
  return !!token;
}

/**
 * Check if guest resume data exists
 */
export function hasGuestResumeData(): boolean {
  if (typeof window === 'undefined') return false;
  const data = localStorage.getItem(GUEST_RESUME_KEY);
  return !!data;
}

/**
 * Get guest email from localStorage
 */
export function getGuestEmail(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(GUEST_EMAIL_KEY);
}

/**
 * Set guest email in localStorage
 */
export function setGuestEmail(email: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(GUEST_EMAIL_KEY, email);
}

/**
 * Get or create guest resume ID
 */
export function getGuestResumeId(): string {
  if (typeof window === 'undefined') return '';
  
  let guestId = localStorage.getItem(GUEST_RESUME_ID_KEY);
  
  if (!guestId) {
    // Generate a new guest ID
    guestId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(GUEST_RESUME_ID_KEY, guestId);
  }
  
  return guestId;
}

/**
 * Save guest resume data to localStorage
 */
export function saveGuestResume(data: Partial<GuestResumeData>): void {
  if (typeof window === 'undefined') return;
  
  const existing = loadGuestResume();
  const updated = {
    ...existing,
    ...data,
    // Merge arrays instead of replacing them
    experiences: data.experiences !== undefined ? data.experiences : existing.experiences,
    educations: data.educations !== undefined ? data.educations : existing.educations,
    skills: data.skills !== undefined ? data.skills : existing.skills,
    projects: data.projects !== undefined ? data.projects : existing.projects,
    certifications: data.certifications !== undefined ? data.certifications : existing.certifications,
    languages: data.languages !== undefined ? data.languages : existing.languages,
    interests: data.interests !== undefined ? data.interests : existing.interests,
  };
  
  localStorage.setItem(GUEST_RESUME_KEY, JSON.stringify(updated));
  
  // Save email if provided in personal data
  if (data.personal?.email) {
    setGuestEmail(data.personal.email);
  }
}

/**
 * Load guest resume data from localStorage
 */
export function loadGuestResume(): GuestResumeData {
  if (typeof window === 'undefined') return {};
  
  const data = localStorage.getItem(GUEST_RESUME_KEY);
  if (!data) return {};
  
  try {
    return JSON.parse(data) as GuestResumeData;
  } catch (error) {
    console.error('Error parsing guest resume data:', error);
    return {};
  }
}

/**
 * Clear guest resume data from localStorage
 */
export function clearGuestResume(): void {
  if (typeof window === 'undefined') return;
  
  localStorage.removeItem(GUEST_RESUME_KEY);
  localStorage.removeItem(GUEST_RESUME_ID_KEY);
  localStorage.removeItem(GUEST_EMAIL_KEY);
}

/**
 * Convert guest resume data to API format
 */
export function guestResumeToApiFormat(): any {
  const guestData = loadGuestResume();
  
  return {
    personal_info: guestData.personal ? {
      full_name: guestData.personal.fullName,
      email: guestData.personal.email,
      phone: guestData.personal.phone,
      location: guestData.personal.location,
      linkedin_url: guestData.personal.linkedin,
      github_url: guestData.personal.github,
      portfolio_url: guestData.personal.portfolio,
    } : undefined,
    summary: guestData.summary?.summary,
    professional_tagline: guestData.summary?.professionalTagline,
    experiences: guestData.experiences?.map(exp => ({
      title: exp.title,
      company: exp.company,
      location: exp.location,
      start_date: exp.startDate,
      end_date: exp.endDate,
      current: exp.current,
      description: exp.description,
      order: exp.order,
    })),
    educations: guestData.educations?.map(edu => ({
      degree: edu.degree,
      school: edu.school,
      location: edu.location,
      start_date: edu.startDate,
      end_date: edu.endDate,
      current: edu.current,
      description: edu.description,
      order: edu.order,
    })),
    skills: guestData.skills?.map(skill => ({
      name: skill.name,
      level: skill.level,
      order: skill.order,
    })),
    projects: guestData.projects?.map(proj => ({
      title: proj.title,
      description: proj.description,
      technologies: proj.technologies,
      start_date: proj.startDate,
      end_date: proj.endDate,
      order: proj.order,
    })),
    certifications: guestData.certifications?.map(cert => ({
      name: cert.name,
      issuer: cert.issuer,
      issue_date: cert.issueDate,
      expiry_date: cert.expiryDate,
      order: cert.order,
    })),
    languages: guestData.languages?.map(lang => ({
      name: lang.name,
      proficiency: lang.proficiency,
      order: lang.order,
    })),
    interests: guestData.interests?.map(int => ({
      name: int.name,
      order: int.order,
    })),
  };
}




