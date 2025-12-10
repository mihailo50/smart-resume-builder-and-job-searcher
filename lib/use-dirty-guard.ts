import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

const DIRTY_STATE_KEY = 'resume_dirty_state';
const DIRTY_SECTIONS_KEY = 'resume_dirty_sections';

/**
 * Global dirty state management
 */
let globalDirtyState = false;
let dirtySections = new Set<string>();

/**
 * Hook to track form dirty state and prevent navigation when unsaved
 */
export function useDirtyGuard(isDirty: boolean, section?: string) {
  const router = useRouter();
  const isDirtyRef = useRef(isDirty);
  const sectionRef = useRef(section);

  useEffect(() => {
    isDirtyRef.current = isDirty;
    sectionRef.current = section;
    
    if (section) {
      if (isDirty) {
        dirtySections.add(section);
      } else {
        dirtySections.delete(section);
      }
      globalDirtyState = dirtySections.size > 0;
    } else {
      globalDirtyState = isDirty;
    }

    // Store in localStorage for persistence
    if (typeof window !== 'undefined') {
      localStorage.setItem(DIRTY_STATE_KEY, String(globalDirtyState));
      localStorage.setItem(DIRTY_SECTIONS_KEY, JSON.stringify(Array.from(dirtySections)));
    }
  }, [isDirty, section]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirtyRef.current || globalDirtyState) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);
}

/**
 * Hook to manually set dirty state
 */
export function useManualDirtyGuard(section: string) {
  const markDirty = () => {
    dirtySections.add(section);
    globalDirtyState = dirtySections.size > 0;

    if (typeof window !== 'undefined') {
      localStorage.setItem(DIRTY_STATE_KEY, String(globalDirtyState));
      localStorage.setItem(DIRTY_SECTIONS_KEY, JSON.stringify(Array.from(dirtySections)));
    }
  };

  const markClean = () => {
    dirtySections.delete(section);
    globalDirtyState = dirtySections.size > 0;

    if (typeof window !== 'undefined') {
      localStorage.setItem(DIRTY_STATE_KEY, String(globalDirtyState));
      localStorage.setItem(DIRTY_SECTIONS_KEY, JSON.stringify(Array.from(dirtySections)));
    }
  };

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (globalDirtyState) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  return { markDirty, markClean };
}

/**
 * Hook to show beforeunload warning for guest users
 */
export function useBeforeUnloadGuard(showWarning: boolean = true) {
  useEffect(() => {
    if (!showWarning) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (globalDirtyState) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [showWarning]);
}

/**
 * Get global dirty state
 */
export function useGlobalDirtyState(): boolean {
  const [dirty, setDirty] = useState(globalDirtyState);

  useEffect(() => {
    const checkDirty = () => {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem(DIRTY_STATE_KEY);
        globalDirtyState = stored === 'true';
        setDirty(globalDirtyState);
      }
    };

    checkDirty();
    const interval = setInterval(checkDirty, 1000);
    return () => clearInterval(interval);
  }, []);

  return dirty;
}

/**
 * Clear all dirty state
 */
export function clearDirtyState(): void {
  globalDirtyState = false;
  dirtySections.clear();

  if (typeof window !== 'undefined') {
    localStorage.removeItem(DIRTY_STATE_KEY);
    localStorage.removeItem(DIRTY_SECTIONS_KEY);
  }
}
