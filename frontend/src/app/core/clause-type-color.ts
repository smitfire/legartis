import type { ClauseType } from './models';

// Tonal colors that work on both light and dark surfaces. Each clause type
// gets a stable hue so the dashboard and document-detail views agree.
const COLORS: Record<ClauseType, { bg: string; fg: string }> = {
  limitation_of_liability: { bg: '#fde2e2', fg: '#7a1f1f' },
  termination_for_convenience: { bg: '#fde7c8', fg: '#7a4318' },
  non_compete: { bg: '#fff4c2', fg: '#6f5806' },
  confidentiality: { bg: '#d8eccf', fg: '#214d12' },
  governing_law: { bg: '#cfe6f9', fg: '#0e3d63' },
  indemnification: { bg: '#e1d8f6', fg: '#3b1f7a' },
  force_majeure: { bg: '#f5d6e9', fg: '#6a1647' },
};

export function clauseTypeColor(clauseType: ClauseType): { bg: string; fg: string } {
  return COLORS[clauseType];
}
