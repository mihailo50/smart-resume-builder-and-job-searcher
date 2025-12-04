'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, Sparkles, FileText } from 'lucide-react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';

export default function CoverLetterPage() {
  const [jobDescription, setJobDescription] = useState('');
  const [tone, setTone] = useState('professional');
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({
        openOnClick: false,
      }),
      Placeholder.configure({
        placeholder: 'Your cover letter will appear here...',
      }),
    ],
    content: '',
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none min-h-[400px] p-4',
      },
    },
  });

  const handleGenerate = async () => {
    if (!jobDescription) return;
    setGenerating(true);
    // Simulate AI generation
    await new Promise((resolve) => setTimeout(resolve, 2000));
    editor?.commands.setContent('<p>Dear Hiring Manager,</p><p>I am writing to express my interest in the position...</p>');
    setGenerated(true);
    setGenerating(false);
  };

  const handleExport = async (format: 'pdf' | 'docx') => {
    // Export logic
    console.log(`Exporting as ${format}`);
  };

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8"
            >
              <h1 className="text-4xl md:text-5xl font-bold mb-4">Cover Letter Generator</h1>
              <p className="text-xl text-muted-foreground">
                Generate a personalized cover letter tailored to the job description
              </p>
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Section */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Job Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Select Resume</Label>
                      <Select defaultValue="resume-1">
                        <SelectTrigger>
                          <SelectValue placeholder="Select a resume" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="resume-1">Software Engineer Resume</SelectItem>
                          <SelectItem value="resume-2">Product Manager Resume</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Job Description</Label>
                      <Textarea
                        placeholder="Paste the job description here..."
                        rows={10}
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                        className="min-h-[200px]"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Tone</Label>
                      <Select value={tone} onValueChange={setTone}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="professional">Professional</SelectItem>
                          <SelectItem value="confident">Confident</SelectItem>
                          <SelectItem value="friendly">Friendly</SelectItem>
                          <SelectItem value="enthusiastic">Enthusiastic</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button
                      onClick={handleGenerate}
                      disabled={!jobDescription || generating}
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
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles className="mr-2 h-4 w-4" />
                          Generate Cover Letter
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Editor Section */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>Cover Letter</CardTitle>
                      {generated && (
                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleExport('pdf')}
                            variant="outline"
                            size="sm"
                          >
                            <Download className="mr-2 h-4 w-4" />
                            PDF
                          </Button>
                          <Button
                            onClick={() => handleExport('docx')}
                            variant="outline"
                            size="sm"
                          >
                            <FileText className="mr-2 h-4 w-4" />
                            DOCX
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="border rounded-lg min-h-[500px]">
                      <EditorContent editor={editor} />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}








