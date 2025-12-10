import { GuestResumeData } from './guest-resume';

/**
 * Convert resume data to plain text format for AI processing
 */
export function convertResumeToText(resume: GuestResumeData): string {
  const sections: string[] = [];

  // Personal Info
  if (resume.personal) {
    const p = resume.personal;
    if (p.fullName) sections.push(`Name: ${p.fullName}`);
    if (p.email) sections.push(`Email: ${p.email}`);
    if (p.phone) sections.push(`Phone: ${p.phone}`);
    if (p.location) sections.push(`Location: ${p.location}`);
    if (p.portfolio) sections.push(`Portfolio: ${p.portfolio}`);
    if (p.linkedin) sections.push(`LinkedIn: ${p.linkedin}`);
    if (p.github) sections.push(`GitHub: ${p.github}`);
  }

  // Summary
  if (resume.summary) {
    if (resume.summary.professionalTagline) {
      sections.push(`\nTagline: ${resume.summary.professionalTagline}`);
    }
    if (resume.summary.summary) {
      sections.push(`\nSummary:\n${resume.summary.summary}`);
    }
  }

  // Experience
  if (resume.experiences && resume.experiences.length > 0) {
    sections.push('\nExperience:');
    resume.experiences.forEach((exp) => {
      sections.push(`\n${exp.title || ''} at ${exp.company || ''}`);
      if (exp.location) sections.push(`Location: ${exp.location}`);
      const dates = [exp.startDate, exp.current ? 'Present' : exp.endDate].filter(Boolean).join(' - ');
      if (dates) sections.push(`Duration: ${dates}`);
      if (exp.description) sections.push(exp.description);
    });
  }

  // Projects
  if (resume.projects && resume.projects.length > 0) {
    sections.push('\nProjects:');
    resume.projects.forEach((proj) => {
      sections.push(`\n${proj.title || ''}`);
      if (proj.description) sections.push(proj.description);
      if (proj.technologies) {
        sections.push(`Technologies: ${proj.technologies}`);
      }
    });
  }

  // Education
  if (resume.educations && resume.educations.length > 0) {
    sections.push('\nEducation:');
    resume.educations.forEach((edu) => {
      sections.push(`\n${edu.degree || ''}`);
      if (edu.school) sections.push(`${edu.school}`);
      if (edu.location) sections.push(`Location: ${edu.location}`);
      const dates = [edu.startDate, edu.current ? 'Present' : edu.endDate].filter(Boolean).join(' - ');
      if (dates) sections.push(`Duration: ${dates}`);
      if (edu.description) sections.push(edu.description);
    });
  }

  // Certifications
  if (resume.certifications && resume.certifications.length > 0) {
    sections.push('\nCertifications:');
    resume.certifications.forEach((cert) => {
      sections.push(`\n${cert.name || ''}`);
      if (cert.issuer) sections.push(`Issued by: ${cert.issuer}`);
      if (cert.issueDate) sections.push(`Date: ${cert.issueDate}`);
    });
  }

  // Skills
  if (resume.skills && resume.skills.length > 0) {
    sections.push('\nSkills:');
    const skillNames = resume.skills.map(s => s.name).filter(Boolean);
    sections.push(skillNames.join(', '));
  }

  // Languages
  if (resume.languages && resume.languages.length > 0) {
    sections.push('\nLanguages:');
    resume.languages.forEach((lang) => {
      sections.push(`${lang.name || ''}${lang.proficiency ? ` (${lang.proficiency})` : ''}`);
    });
  }

  // Interests
  if (resume.interests && resume.interests.length > 0) {
    sections.push('\nInterests:');
    sections.push(resume.interests.map(i => i.name).filter(Boolean).join(', '));
  }

  return sections.join('\n');
}

/**
 * Check if resume has enough content for AI optimization
 */
export function hasResumeContent(resume: GuestResumeData): boolean {
  const hasPersonal = resume.personal && (
    resume.personal.fullName ||
    resume.personal.email
  );
  
  const hasExperience = resume.experiences && resume.experiences.length > 0;
  const hasEducation = resume.educations && resume.educations.length > 0;
  const hasSkills = resume.skills && resume.skills.length > 0;
  
  // At minimum, need personal info and one of the main sections
  return !!(hasPersonal && (hasExperience || hasEducation || hasSkills));
}
