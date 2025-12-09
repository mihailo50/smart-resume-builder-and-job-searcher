'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const STEPS = [
  { id: 1, name: 'Personal Info', href: '/builder/personal' },
  { id: 2, name: 'Experience', href: '/builder/experience' },
  { id: 3, name: 'Projects', href: '/builder/projects' },
  { id: 4, name: 'Education', href: '/builder/education' },
  { id: 5, name: 'Certifications', href: '/builder/certifications' },
  { id: 6, name: 'Skills', href: '/builder/skills' },
  { id: 7, name: 'Languages', href: '/builder/languages' },
  { id: 8, name: 'Interests', href: '/builder/interests' },
  { id: 9, name: 'Summary', href: '/builder/summary' },
  { id: 10, name: 'AI Optimize', href: '/builder/optimize' },
  { id: 11, name: 'Preview', href: '/builder/preview' },
];

interface Props {
  currentStepId: number;
  resumeId?: string | null;
  guestId?: string | null;
}

export function ResumeStepsSidebar({ currentStepId, resumeId, guestId }: Props) {
  const suffix = resumeId ? `?id=${resumeId}` : guestId ? `?guestId=${guestId}` : '';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Resume Builder</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {STEPS.map((step) => {
          const href = suffix ? `${step.href}${suffix}` : step.href;
          const isCurrent = step.id === currentStepId;
          return (
            <Link
              key={step.id}
              href={href}
              className={`flex items-center gap-2 p-2 rounded-md transition-colors ${
                isCurrent ? 'bg-primary/10 text-primary font-semibold' : 'text-muted-foreground hover:bg-accent'
              }`}
            >
              <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary">
                {step.id}
              </div>
              <span className="text-sm">{step.name}</span>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}
