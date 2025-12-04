'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Sparkles, Loader2, CheckCircle2, X, AlertCircle } from 'lucide-react';

interface AISummaryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  originalSummary: string;
  onAccept: (enhancedSummary: string) => void;
  enhancedSummary?: string;
  isGenerating?: boolean;
  error?: string;
}

export function AISummaryModal({
  open,
  onOpenChange,
  originalSummary,
  onAccept,
  enhancedSummary,
  isGenerating = false,
  error,
}: AISummaryModalProps) {
  const [showComparison, setShowComparison] = useState(false);

  const handleAccept = () => {
    if (enhancedSummary) {
      onAccept(enhancedSummary);
      onOpenChange(false);
    }
  };

  const handleReject = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            AI-Enhanced Summary
          </DialogTitle>
          <DialogDescription>
            {isGenerating
              ? 'Our AI is enhancing your summary...'
              : 'Review the enhanced summary and decide if you want to use it.'}
          </DialogDescription>
        </DialogHeader>

        {isGenerating ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <p className="text-muted-foreground">Enhancing your summary with AI...</p>
          </div>
        ) : error ? (
          <div className="bg-destructive/10 text-destructive p-4 rounded-lg flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
        ) : enhancedSummary ? (
          <div className="space-y-4 mt-4">
            {/* Toggle to show/hide original */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Enhanced Summary</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowComparison(!showComparison)}
              >
                {showComparison ? 'Hide' : 'Show'} Original
              </Button>
            </div>

            {/* Enhanced Summary */}
            <div className="space-y-2">
              <Textarea
                readOnly
                value={enhancedSummary}
                rows={8}
                className="min-h-[150px] bg-primary/5 border-primary/20"
              />
              <p className="text-xs text-muted-foreground">
                {enhancedSummary.length} characters (no limit)
              </p>
            </div>

            {/* Original Summary (if toggled) */}
            {showComparison && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2 pt-4 border-t"
              >
                <span className="text-sm font-medium text-muted-foreground">Original Summary</span>
                <Textarea
                  readOnly
                  value={originalSummary || '(empty)'}
                  rows={6}
                  className="min-h-[100px] bg-muted/50"
                />
              </motion.div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t">
              <Button
                variant="outline"
                onClick={handleReject}
                className="flex-1"
              >
                <X className="mr-2 h-4 w-4" />
                Keep Original
              </Button>
              <Button
                onClick={handleAccept}
                className="flex-1 bg-gradient-to-r from-primary to-secondary"
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Use Enhanced
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            No enhanced summary available
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}


