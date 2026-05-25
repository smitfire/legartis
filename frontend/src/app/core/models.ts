export type ClauseType =
  | 'limitation_of_liability'
  | 'termination_for_convenience'
  | 'non_compete'
  | 'confidentiality'
  | 'governing_law'
  | 'indemnification'
  | 'force_majeure';

export type LabelSource = 'MANUAL' | 'AUTO';

export interface ClauseTypeOption {
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

export interface DocumentDetail {
  id: number;
  title: string;
  uploaded_at: string;
  sentences: Sentence[];
}

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
