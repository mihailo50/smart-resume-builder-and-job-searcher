import './globals.css';
import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from '@/lib/providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'ResumeAI Pro – Smart Resume Builder & Job Matcher',
  description:
    'Build ATS-optimized resumes, get personalized improvements, and match with real job postings in seconds. Land your dream job 10× faster with AI.',
  keywords: ['resume builder', 'ATS optimizer', 'job matcher', 'AI resume', 'career tools'],
  authors: [{ name: 'ResumeAI Pro' }],
  creator: 'ResumeAI Pro',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://resumeai.pro',
    title: 'ResumeAI Pro – Smart Resume Builder & Job Matcher',
    description:
      'Build ATS-optimized resumes, get personalized improvements, and match with real job postings in seconds.',
    siteName: 'ResumeAI Pro',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ResumeAI Pro – Smart Resume Builder & Job Matcher',
    description:
      'Build ATS-optimized resumes, get personalized improvements, and match with real job postings in seconds.',
  },
  manifest: '/manifest.json',
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#6366f1' },
    { media: '(prefers-color-scheme: dark)', color: '#6366f1' },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
