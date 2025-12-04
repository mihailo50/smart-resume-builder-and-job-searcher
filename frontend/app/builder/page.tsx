'use client';

import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight, FileText, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';

const steps = [
  { id: 1, name: 'Personal Info', href: '/builder/personal', completed: false },
  { id: 2, name: 'Experience', href: '/builder/experience', completed: false },
  { id: 3, name: 'Projects', href: '/builder/projects', completed: false },
  { id: 4, name: 'Education', href: '/builder/education', completed: false },
  { id: 5, name: 'Certifications', href: '/builder/certifications', completed: false },
  { id: 6, name: 'Skills', href: '/builder/skills', completed: false },
  { id: 7, name: 'Languages', href: '/builder/languages', completed: false },
  { id: 8, name: 'Interests', href: '/builder/interests', completed: false },
  { id: 9, name: 'Summary', href: '/builder/summary', completed: false },
  { id: 10, name: 'AI Optimize', href: '/builder/optimize', completed: false },
  { id: 11, name: 'Preview & Export', href: '/builder/preview', completed: false },
];

export default function BuilderPage() {
  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto"
          >
            <div className="text-center mb-12">
              <h1 className="text-4xl md:text-5xl font-bold mb-4">
                Resume Builder
              </h1>
              <p className="text-xl text-muted-foreground">
                Build your professional resume step by step
              </p>
            </div>

            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Build Your Resume
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {steps.map((step, index) => (
                    <motion.div
                      key={step.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center gap-4 p-4 rounded-lg border hover:bg-accent transition-colors"
                    >
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold">
                        {step.completed ? (
                          <CheckCircle2 className="h-5 w-5" />
                        ) : (
                          step.id
                        )}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold">{step.name}</h3>
                      </div>
                      <Button asChild variant="outline" size="sm">
                        <Link href={step.href}>
                          Start
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Link>
                      </Button>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="text-center">
              <Button asChild size="lg" className="bg-gradient-to-r from-primary to-secondary">
                <Link href="/builder/personal">
                  Start Building
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </div>
    </PageTransition>
  );
}








