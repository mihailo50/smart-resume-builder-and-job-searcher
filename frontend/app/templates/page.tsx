'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, CheckCircle2 } from 'lucide-react';
import { TEMPLATES, getCategories, type TemplateId } from '@/lib/templates';
import Image from 'next/image';

// Get API URL for PDF previews
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const TEMPLATE_CATEGORIES = ['All', ...getCategories()];

export default function TemplatesPage() {
  const router = useRouter();
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const filteredTemplates =
    selectedCategory === 'All'
      ? TEMPLATES
      : TEMPLATES.filter((template) => template.category === selectedCategory);

  const handleUseTemplate = (templateId: TemplateId) => {
    // Navigate to builder with template selected
    router.push(`/builder/personal?template=${templateId}`);
  };

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-7xl mx-auto"
          >
            <div className="text-center mb-12">
              <h1 className="text-4xl md:text-5xl font-bold mb-4">
                Resume Templates
              </h1>
              <p className="text-xl text-muted-foreground mb-6">
                Choose from 8 stunning, ATS-optimized templates
              </p>

              {/* Category Filter */}
              <div className="flex flex-wrap justify-center gap-2 mb-8">
                {TEMPLATE_CATEGORIES.map((category) => (
                  <Button
                    key={category}
                    variant={selectedCategory === category ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory(category)}
                    className="rounded-full"
                  >
                    {category}
                  </Button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredTemplates.map((template, index) => (
                <motion.div
                  key={template.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ y: -8, scale: 1.02 }}
                >
                    <Card className="h-full hover:border-primary transition-all flex flex-col">
                    <CardHeader>
                      <div className="aspect-[3/4] bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg flex items-center justify-center mb-4 relative overflow-hidden border">
                        {/* Template Thumbnail - PNG image from backend API */}
                        {template.thumbnail ? (
                          <Image
                            src={template.thumbnail}
                            alt={`${template.name} thumbnail`}
                            fill
                            className="object-contain p-2"
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                            unoptimized={template.thumbnail.includes('localhost') || template.thumbnail.includes('127.0.0.1')}
                            onError={(e) => {
                              // Hide image on error, show fallback
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : null}
                        {/* Fallback gradient background (shown if image fails to load) */}
                        <div
                          className="absolute inset-0 w-full h-full pointer-events-none"
                          style={{
                            background: `linear-gradient(135deg, ${template.colors[0]}15, ${template.colors[1] || template.colors[0]}15)`,
                            zIndex: -1,
                          }}
                        >
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-2xl font-bold opacity-20" style={{ color: template.colors[0] }}>
                              {template.name.split(' ')[0]}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-start justify-between mb-2">
                        <CardTitle className="text-xl">{template.name}</CardTitle>
                        <Badge variant="secondary" className="text-xs">
                          {template.category}
                        </Badge>
                      </div>
                      <CardDescription className="text-sm line-clamp-2 mb-3">
                        {template.description}
                      </CardDescription>
                      <div className="flex flex-wrap gap-1 mb-4">
                        {template.bestFor.slice(0, 2).map((role) => (
                          <Badge key={role} variant="outline" className="text-xs">
                            {role}
                          </Badge>
                        ))}
                        {template.bestFor.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{template.bestFor.length - 2}
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="mt-auto">
                      <Button
                        className="w-full bg-gradient-to-r from-primary to-secondary"
                        onClick={() => handleUseTemplate(template.id)}
                      >
                        <Sparkles className="mr-2 h-4 w-4" />
                        Use Template
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>

            {filteredTemplates.length === 0 && (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No templates found in this category.</p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </PageTransition>
  );
}


