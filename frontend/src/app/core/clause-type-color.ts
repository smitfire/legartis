import type { ClauseType } from './models';

/**
 * Background/foreground pair to render a badge for a clause type.
 *
 * The seven original seed values keep their hand-picked colours so the
 * dashboard looks identical post-migration. User-created clause types get
 * deterministically assigned a hue from `PALETTE` based on a stable hash of
 * their machine value — overlap is accepted as a tradeoff for unbounded
 * dynamic types.
 */
const SEED_COLORS: Readonly<Record<string, { bg: string; fg: string }>> = {
  limitation_of_liability: { bg: '#fde2e2', fg: '#7a1f1f' },
  termination_for_convenience: { bg: '#fde7c8', fg: '#7a4318' },
  non_compete: { bg: '#fff4c2', fg: '#6f5806' },
  confidentiality: { bg: '#d8eccf', fg: '#214d12' },
  governing_law: { bg: '#cfe6f9', fg: '#0e3d63' },
  indemnification: { bg: '#e1d8f6', fg: '#3b1f7a' },
  force_majeure: { bg: '#f5d6e9', fg: '#6a1647' },
};

const PALETTE: ReadonlyArray<{ bg: string; fg: string }> = [
  { bg: '#d2efe6', fg: '#11463c' },
  { bg: '#f0d9b9', fg: '#5e3a0d' },
  { bg: '#dcd6f7', fg: '#2a2161' },
  { bg: '#fbd1cb', fg: '#6b2014' },
  { bg: '#cfe9c5', fg: '#1f4d1f' },
];

export function clauseTypeColor(clauseType: ClauseType): { bg: string; fg: string } {
  const seeded = SEED_COLORS[clauseType];
  if (seeded) return seeded;
  let hash = 0;
  for (const ch of clauseType) {
    hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  }
  return PALETTE[hash % PALETTE.length];
}
