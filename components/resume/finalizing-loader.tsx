'use client';

import { motion } from 'framer-motion';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface FinalizingLoaderProps {
  progress: number;
  currentStep: string;
  isComplete?: boolean;
}

export function FinalizingLoader({ progress, currentStep, isComplete = false }: FinalizingLoaderProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md mx-4"
      >
        <div className="bg-card border rounded-lg p-8 shadow-lg">
          <div className="flex flex-col items-center justify-center space-y-6">
            {isComplete ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200 }}
              >
                <CheckCircle2 className="h-16 w-16 text-primary" />
              </motion.div>
            ) : (
              <Loader2 className="h-16 w-16 animate-spin text-primary" />
            )}
            
            <div className="text-center space-y-2">
              <h3 className="text-2xl font-bold">
                {isComplete ? 'Resume Saved!' : 'Finalizing your resume...'}
              </h3>
              <p className="text-muted-foreground">{currentStep}</p>
            </div>
            
            <div className="w-full space-y-2">
              <Progress value={progress} className="h-2" />
              <p className="text-xs text-center text-muted-foreground">
                {Math.round(progress)}% complete
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}




