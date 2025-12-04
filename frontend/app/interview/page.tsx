'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Sparkles, Mic, CheckCircle2, Star } from 'lucide-react';

const sampleQuestions = [
  {
    id: 1,
    type: 'behavioral',
    question: 'Tell me about a time when you faced a challenging deadline.',
    star: true,
  },
  {
    id: 2,
    type: 'technical',
    question: 'Explain how React hooks work and when you would use them.',
    star: false,
  },
  {
    id: 3,
    type: 'behavioral',
    question: 'Describe a situation where you had to work with a difficult team member.',
    star: true,
  },
];

export default function InterviewPage() {
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [generating, setGenerating] = useState(false);
  const [questions, setQuestions] = useState<typeof sampleQuestions>([]);

  const handleGenerate = async () => {
    if (!jobTitle || !company) return;
    setGenerating(true);
    // Simulate AI generation
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setQuestions(sampleQuestions);
    setGenerating(false);
  };

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8 text-center"
            >
              <h1 className="text-4xl md:text-5xl font-bold mb-4">Interview Prep</h1>
              <p className="text-xl text-muted-foreground">
                Get personalized interview questions and practice your answers
              </p>
            </motion.div>

            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Job Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Job Title</Label>
                    <Input
                      placeholder="Software Engineer"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Company</Label>
                    <Input
                      placeholder="Tech Corp"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                    />
                  </div>
                </div>
                <Button
                  onClick={handleGenerate}
                  disabled={!jobTitle || !company || generating}
                  className="w-full bg-gradient-to-r from-primary to-secondary"
                >
                  {generating ? (
                    <>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        className="mr-2"
                      >
                        <Sparkles className="h-4 w-4" />
                      </motion.div>
                      Generating Questions...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Generate Interview Questions
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {questions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Star className="h-5 w-5 text-primary" />
                      Interview Questions ({questions.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Accordion type="single" collapsible className="w-full">
                      {questions.map((q, index) => (
                        <AccordionItem key={q.id} value={`item-${q.id}`}>
                          <AccordionTrigger>
                            <div className="flex items-center gap-3">
                              <Badge variant={q.type === 'behavioral' ? 'default' : 'secondary'}>
                                {q.type}
                              </Badge>
                              <span className="text-left">{q.question}</span>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="space-y-4 pt-2">
                              <div className="p-4 rounded-lg bg-muted/50 border border-primary/20">
                                <h4 className="font-semibold mb-2">STAR Method Guide:</h4>
                                <ul className="space-y-1 text-sm text-muted-foreground list-disc list-inside">
                                  <li><strong>Situation:</strong> Set the context</li>
                                  <li><strong>Task:</strong> Describe your responsibility</li>
                                  <li><strong>Action:</strong> Explain what you did</li>
                                  <li><strong>Result:</strong> Share the outcome</li>
                                </ul>
                              </div>
                              <Textarea
                                placeholder="Write your answer here..."
                                rows={6}
                              />
                              <div className="flex gap-2">
                                <Button variant="outline" size="sm">
                                  <Mic className="mr-2 h-4 w-4" />
                                  Record Answer
                                </Button>
                                <Button variant="outline" size="sm">
                                  Get AI Feedback
                                </Button>
                              </div>
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </PageTransition>
  );
}








