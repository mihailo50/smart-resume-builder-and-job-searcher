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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-h-[400px] overflow-y-auto p-2">
          {(showAllTemplates ? TEMPLATES : TEMPLATES.slice(0, 4)).map((template) => (
            <Card
              key={template.id}
              className={`cursor-pointer transition-all hover:border-primary ${
                selectedTemplate === template.id ? 'border-primary border-2' : ''
              }`}
              onClick={() => onTemplateChange(template.id)}
            >
              <CardHeader className="p-2">
                <div className="aspect-[3/4] bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg mb-2 relative overflow-hidden border">
                  <Image
                    src={template.thumbnail}
                    alt={template.name}
                    fill
                    className="object-contain p-1"
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
        {!showAllTemplates && TEMPLATES.length > 4 && (
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
        <RadioGroup value={selectedFont} onValueChange={(value) => onFontChange(value as FontCombination)}>
          <div className="space-y-3">
            {Object.entries(FONT_COMBINATIONS).map(([key, font]) => (
              <div key={key} className="flex items-start space-x-3">
                <RadioGroupItem value={key} id={key} className="mt-1" />
                <Label htmlFor={key} className="flex-1 cursor-pointer">
                  <div className="font-medium">{font.name}</div>
                  <div className="text-sm text-muted-foreground">{font.description}</div>
                </Label>
              </div>
            ))}
          </div>
        </RadioGroup>
      </div>

      {/* ATS Mode Toggle */}
      <div className="flex items-center justify-between p-4 border rounded-lg">
        <div className="space-y-0.5">
          <Label htmlFor="ats-mode" className="text-base font-semibold">
            ATS-Friendly Mode
          </Label>
          <div className="text-sm text-muted-foreground">
            Optimize for Applicant Tracking Systems (minimal styling, no graphics)
          </div>
        </div>
        <Switch id="ats-mode" checked={atsMode} onCheckedChange={onAtsModeChange} />
      </div>

      {/* Photo URL (Optional) */}
      {onPhotoUrlChange && (
        <div>
          <Label htmlFor="photo-url" className="text-base font-semibold mb-2 block">
            Profile Photo URL (Optional)
          </Label>
          <input
            id="photo-url"
            type="url"
            value={photoUrl || ''}
            onChange={(e) => onPhotoUrlChange(e.target.value)}
            placeholder="https://example.com/photo.jpg"
            className="w-full px-3 py-2 border rounded-md text-sm"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Enter a URL to your profile photo. Leave empty to use initials.
          </p>
        </div>
      )}
    </div>
  );
}

