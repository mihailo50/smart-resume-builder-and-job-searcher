'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TEMPLATES, FONT_COMBINATIONS, type TemplateId, type FontCombination } from '@/lib/templates';
import { Sparkles, CheckCircle2 } from 'lucide-react';
import Image from 'next/image';

interface TemplateSelectorProps {
  selectedTemplate: TemplateId;
  onTemplateChange: (template: TemplateId) => void;
  selectedFont: FontCombination;
  onFontChange: (font: FontCombination) => void;
  atsMode: boolean;
  onAtsModeChange: (ats: boolean) => void;
  photoUrl?: string;
  onPhotoUrlChange?: (url: string) => void;
}

export function TemplateSelector({
  selectedTemplate,
  onTemplateChange,
  selectedFont,
  onFontChange,
  atsMode,
  onAtsModeChange,
  photoUrl,
  onPhotoUrlChange,
}: TemplateSelectorProps) {
  const [showAllTemplates, setShowAllTemplates] = useState(false);

  return (
    <div className="space-y-6">
      {/* Template Selection */}
      <div>
        <Label className="text-base font-semibold mb-4 block">Choose Template</Label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-[500px] overflow-y-auto p-2">
          {(showAllTemplates ? TEMPLATES : TEMPLATES.slice(0, 6)).map((template) => (
            <Card
              key={template.id}
              className={`cursor-pointer transition-all hover:border-primary ${
                selectedTemplate === template.id ? 'border-primary border-2' : ''
              }`}
              onClick={() => onTemplateChange(template.id)}
            >
              <CardHeader className="p-3">
                <div className="aspect-[3/4] bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg mb-2 relative overflow-hidden border min-h-[220px]">
                  <Image
                    src={template.thumbnail}
                    alt={template.name}
                    fill
                    className="object-cover p-0 scale-[1.02]"
                    onError={(e) => {
                      const target = e.currentTarget as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                  <div
                    className="absolute inset-0"
                    style={{
                      background: `linear-gradient(135deg, ${template.colors[0]}15, ${template.colors[1] || template.colors[0]}15)`,
                    }}
                  >
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs font-bold opacity-20" style={{ color: template.colors[0] }}>
                        {template.name.split(' ')[0]}
                      </span>
                    </div>
                  </div>
                  {selectedTemplate === template.id && (
                    <div className="absolute top-1 right-1 z-10">
                      <CheckCircle2 className="h-4 w-4 text-primary fill-primary bg-white rounded-full" />
                    </div>
                  )}
                </div>
                <CardTitle className="text-xs font-semibold leading-tight">{template.name}</CardTitle>
                <CardDescription className="text-xs line-clamp-1 opacity-70">{template.category}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
        {!showAllTemplates && TEMPLATES.length > 6 && (
          <Button
            variant="outline"
            size="sm"
            className="mt-3 w-full"
            onClick={() => setShowAllTemplates(true)}
          >
            Show All {TEMPLATES.length} Templates
          </Button>
        )}
      </div>

      {/* Font Selection */}
      <div>
        <Label className="text-base font-semibold mb-3 block">Font Combination</Label>
        <Select 
          value={typeof selectedFont === 'string' ? selectedFont : (selectedFont?.label || FONT_COMBINATIONS[0].label)} 
          onValueChange={(value) => {
            const font = FONT_COMBINATIONS.find(f => f.label === value);
            if (font) {
              onFontChange(font);
            } else {
              // Fallback: map string values to font objects
              const fontMap: Record<string, FontCombination> = {
                'modern': FONT_COMBINATIONS[0],
                'classic': FONT_COMBINATIONS[1],
                'creative': FONT_COMBINATIONS[2],
              };
              onFontChange(fontMap[value] || FONT_COMBINATIONS[0]);
            }
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select font combination" />
          </SelectTrigger>
          <SelectContent>
            {FONT_COMBINATIONS.map((font, index) => (
              <SelectItem key={index} value={font.label}>
                {font.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground mt-2">
          {typeof selectedFont === 'string' 
            ? FONT_COMBINATIONS.find(f => f.heading === selectedFont)?.label || selectedFont
            : selectedFont?.label || FONT_COMBINATIONS[0].label}
        </p>
      </div>

      {/* ATS Mode Toggle */}
      <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/30">
        <div className="space-y-0.5 flex-1">
          <Label htmlFor="ats-mode" className="text-base font-semibold cursor-pointer">
            ATS-Friendly Mode
          </Label>
          <div className="text-sm text-muted-foreground">
            {atsMode 
              ? '✓ Removes graphics, QR codes, and complex styling for better ATS parsing'
              : 'Optimize for Applicant Tracking Systems (minimal styling, no graphics)'}
          </div>
        </div>
        <Switch id="ats-mode" checked={atsMode} onCheckedChange={onAtsModeChange} />
      </div>

      {/* Photo Upload/URL (Optional) */}
      {onPhotoUrlChange && (
        <div className="space-y-3">
          <Label className="text-base font-semibold mb-2 block">
            Profile Photo (Optional)
          </Label>
          
          {/* File Upload */}
          <div>
            <Label htmlFor="photo-upload" className="text-sm font-medium mb-1 block">
              Upload Photo
            </Label>
            <input
              id="photo-upload"
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  // Convert to data URL for preview
                  const reader = new FileReader();
                  reader.onload = (event) => {
                    const dataUrl = event.target?.result as string;
                    onPhotoUrlChange(dataUrl);
                  };
                  reader.readAsDataURL(file);
                }
              }}
              className="w-full px-3 py-2 border rounded-md text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
            />
          </div>
          
          {/* Or URL */}
          <div>
            <Label htmlFor="photo-url" className="text-sm font-medium mb-1 block">
              Or Enter Photo URL
            </Label>
            <input
              id="photo-url"
              type="url"
              value={photoUrl || ''}
              onChange={(e) => onPhotoUrlChange(e.target.value)}
              placeholder="https://example.com/photo.jpg"
              className="w-full px-3 py-2 border rounded-md text-sm"
            />
          </div>
          
          {/* Preview */}
          {photoUrl && (
            <div className="mt-2">
              <img
                src={photoUrl}
                alt="Profile preview"
                className="w-24 h-24 object-cover rounded-full border-2 border-primary"
                onError={() => onPhotoUrlChange('')}
              />
            </div>
          )}
          
          <p className="text-xs text-muted-foreground">
            Upload a photo or enter a URL. Leave empty to use initials.
          </p>
        </div>
      )}
    </div>
  );
}

