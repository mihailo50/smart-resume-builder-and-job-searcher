const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export type TemplateId = 
  | 'modern-indigo'
  | 'sidebar-teal'
  | 'ats-classic'
  | 'executive-gold'
  | 'creative-violet'
  | 'minimalist-black'
  | 'tech-cyan'
  | 'elegant-emerald';

export type FontCombination = {
  heading: string;
  body: string;
  label: string;
};

export interface Template {
  id: TemplateId;
  name: string;
  category: string;
  description: string;
  thumbnail: string;
  colors: string[];
  bestFor: string[];
}

export const TEMPLATES: Template[] = [
  {
    id: 'modern-indigo',
    name: 'Modern Indigo',
    category: 'Modern',
    description: 'Clean and contemporary design with a professional indigo color scheme. Perfect for tech and creative industries.',
    thumbnail: `${API_URL}/v1/templates/modern-indigo/thumbnail/`,
    colors: ['#6366f1', '#8b5cf6'],
    bestFor: ['Software Engineer', 'Designer', 'Product Manager', 'Developer'],
  },
  {
    id: 'sidebar-teal',
    name: 'Sidebar Teal',
    category: 'Creative',
    description: 'Unique sidebar layout with teal accents. Great for showcasing skills and experience in a visually appealing way.',
    thumbnail: `${API_URL}/v1/templates/sidebar-teal/thumbnail/`,
    colors: ['#14b8a6', '#06b6d4'],
    bestFor: ['Marketing', 'Sales', 'Creative Director', 'Consultant'],
  },
  {
    id: 'ats-classic',
    name: 'ATS Classic',
    category: 'Professional',
    description: 'Optimized for Applicant Tracking Systems. Simple, clean layout that ensures maximum compatibility.',
    thumbnail: `${API_URL}/v1/templates/ats-classic/thumbnail/`,
    colors: ['#1e40af', '#3b82f6'],
    bestFor: ['Any Industry', 'Corporate', 'Finance', 'Healthcare'],
  },
  {
    id: 'executive-gold',
    name: 'Executive Gold',
    category: 'Executive',
    description: 'Premium design with gold accents. Ideal for senior executives and C-level positions.',
    thumbnail: `${API_URL}/v1/templates/executive-gold/thumbnail/`,
    colors: ['#d97706', '#f59e0b'],
    bestFor: ['CEO', 'Executive', 'Director', 'VP'],
  },
  {
    id: 'creative-violet',
    name: 'Creative Violet',
    category: 'Creative',
    description: 'Bold and vibrant design perfect for creative professionals who want to stand out.',
    thumbnail: `${API_URL}/v1/templates/creative-violet/thumbnail/`,
    colors: ['#7c3aed', '#a855f7'],
    bestFor: ['Artist', 'Designer', 'Writer', 'Photographer'],
  },
  {
    id: 'minimalist-black',
    name: 'Minimalist Black',
    category: 'Minimal',
    description: 'Ultra-minimal design with black and white color scheme. Perfect for those who prefer simplicity.',
    thumbnail: `${API_URL}/v1/templates/minimalist-black/thumbnail/`,
    colors: ['#000000', '#1f2937'],
    bestFor: ['Architect', 'Engineer', 'Analyst', 'Researcher'],
  },
  {
    id: 'tech-cyan',
    name: 'Tech Cyan',
    category: 'Tech',
    description: 'Modern tech-focused design with cyan accents. Great for software engineers and tech professionals.',
    thumbnail: `${API_URL}/v1/templates/tech-cyan/thumbnail/`,
    colors: ['#06b6d4', '#0891b2'],
    bestFor: ['Software Engineer', 'Data Scientist', 'DevOps', 'QA Engineer'],
  },
  {
    id: 'elegant-emerald',
    name: 'Elegant Emerald',
    category: 'Elegant',
    description: 'Sophisticated design with emerald green accents. Perfect for professionals in consulting and business.',
    thumbnail: `${API_URL}/v1/templates/elegant-emerald/thumbnail/`,
    colors: ['#059669', '#10b981'],
    bestFor: ['Consultant', 'Business Analyst', 'Manager', 'Strategist'],
  },
];

export const FONT_COMBINATIONS: FontCombination[] = [
  {
    heading: 'Inter',
    body: 'Inter',
    label: 'Inter (Modern)',
  },
  {
    heading: 'Roboto',
    body: 'Roboto',
    label: 'Roboto (Clean)',
  },
  {
    heading: 'Lato',
    body: 'Lato',
    label: 'Lato (Friendly)',
  },
  {
    heading: 'Open Sans',
    body: 'Open Sans',
    label: 'Open Sans (Readable)',
  },
  {
    heading: 'Montserrat',
    body: 'Montserrat',
    label: 'Montserrat (Bold)',
  },
  {
    heading: 'Playfair Display',
    body: 'Source Sans Pro',
    label: 'Playfair + Source Sans (Elegant)',
  },
  {
    heading: 'Merriweather',
    body: 'Merriweather',
    label: 'Merriweather (Classic)',
  },
  {
    heading: 'Poppins',
    body: 'Poppins',
    label: 'Poppins (Modern)',
  },
];

export function getCategories(): string[] {
  const categories = new Set(TEMPLATES.map((template) => template.category));
  return Array.from(categories).sort();
}

export function getTemplateById(id: TemplateId): Template | undefined {
  return TEMPLATES.find((template) => template.id === id);
}

export function getTemplatesByCategory(category: string): Template[] {
  if (category === 'All') return TEMPLATES;
  return TEMPLATES.filter((template) => template.category === category);
}


