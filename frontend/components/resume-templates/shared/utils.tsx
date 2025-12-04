import React from 'react';

export function formatDateStr(date?: string): string {
  if (!date) return '';
  try {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  } catch {
    return date;
  }
}

export function formatDescription(text?: string): React.ReactNode {
  if (!text) return null;
  const lines = text.split('\n').filter((l) => l.trim());
  return (
    <ul className="list-none pl-0 space-y-1">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        const isBullet = /^[•\-\*]\s/.test(trimmed);
        const content = isBullet ? trimmed.substring(2) : trimmed;
        return (
          <li key={idx} className="relative pl-4 text-sm text-slate-600 leading-relaxed">
            <span className="absolute left-0 text-teal-500 font-bold text-base">•</span>
            {content}
          </li>
        );
      })}
    </ul>
  );
}

