/**
 * Machine identifier for a clause type. Used to be a closed string-union over the
 * seven seed values; with dynamic clause-type CRUD it's just a stable string. The
 * full option (with display label + numeric id) is fetched from the backend.
 */
export type ClauseType = string;

/**
 * Provenance of a label. `MANUAL` is a human assignment; `AUTO` is reserved for
 * future ML-suggested labels (not produced today, but the API surfaces it).
 */
export type LabelSource = 'MANUAL' | 'AUTO';

export interface ClauseTypeOption {
  id: number;
  value: ClauseType;
  label: string;
}

export interface ClauseTypeCount extends ClauseTypeOption {
  count: number;
}

export interface Label {
  id: number;
  sentence_id: number;
  clause_type: ClauseType;
  source: LabelSource;
  confidence: number | null;
  created_at: string;
}

export interface Sentence {
  id: number;
  position: number;
  text: string;
  labels: Label[];
}

/**
 * Full document payload including every sentence and its labels. Returned by
 * the detail endpoint; use for the document detail view.
 */
export interface DocumentDetail {
  id: number;
  title: string;
  uploaded_at: string;
  sentences: Sentence[];
}

/**
 * Lightweight document row for list/dashboard views — counts and clause-type
 * tags only, no sentence bodies. Fetch `DocumentDetail` when text is needed.
 */
export interface DocumentSummary {
  id: number;
  title: string;
  uploaded_at: string;
  sentence_count: number;
  label_count: number;
  clause_types: ClauseType[];
}

export interface DocumentGroup {
  clause_type: ClauseType;
  documents: DocumentSummary[];
}

export interface GroupedDocuments {
  groups: DocumentGroup[];
}
