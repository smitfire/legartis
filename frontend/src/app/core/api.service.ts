import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import type {
  ClauseType,
  ClauseTypeCount,
  ClauseTypeOption,
  DocumentDetail,
  DocumentSummary,
  GroupedDocuments,
  Label,
} from './models';

/**
 * Server-side dashboard filters. All fields are optional and map 1:1 to the
 * `q`, `type` (repeatable), and `group_by` query params on `/api/documents`.
 */
export interface DashboardFilters {
  q?: string;
  types?: ClauseType[];
  groupBy?: 'type';
}

/**
 * Thin wrapper over the FastAPI backend. All search/filter/grouping is
 * server-side via query params — keep client-side post-processing out of here.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api';

  listClauseTypes(): Observable<ClauseTypeOption[]> {
    return this.http.get<ClauseTypeOption[]>(`${this.base}/clause-types`);
  }

  /** Counts per clause type, optionally narrowed by the same `q` text filter. */
  listClauseTypeCounts(q?: string): Observable<ClauseTypeCount[]> {
    let params = new HttpParams();
    if (q) params = params.set('q', q);
    return this.http.get<ClauseTypeCount[]>(`${this.base}/clause-type-counts`, { params });
  }

  /**
   * Returns a flat `DocumentSummary[]` by default, or a `GroupedDocuments`
   * envelope when `groupBy: 'type'` is set. Callers must narrow the union.
   */
  listDocuments(filters: DashboardFilters = {}): Observable<DocumentSummary[] | GroupedDocuments> {
    let params = new HttpParams();
    if (filters.q) params = params.set('q', filters.q);
    if (filters.types?.length) {
      for (const t of filters.types) {
        params = params.append('type', t);
      }
    }
    if (filters.groupBy) params = params.set('group_by', filters.groupBy);
    return this.http.get<DocumentSummary[] | GroupedDocuments>(`${this.base}/documents`, {
      params,
    });
  }

  getDocument(id: number): Observable<DocumentDetail> {
    return this.http.get<DocumentDetail>(`${this.base}/documents/${id}`);
  }

  /** Uploads a plain-text or markdown file; the backend tokenises into sentences. */
  uploadDocument(file: File): Observable<DocumentDetail> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    return this.http.post<DocumentDetail>(`${this.base}/documents`, formData);
  }

  /**
   * Attaches a clause type to a sentence. Idempotent on `(sentence_id,
   * clause_type)`: the backend returns the existing label on a 409 conflict
   * rather than creating a duplicate, so callers can treat both as success.
   */
  createLabel(sentenceId: number, clauseType: ClauseType): Observable<Label> {
    return this.http.post<Label>(`${this.base}/sentences/${sentenceId}/labels`, {
      clause_type: clauseType,
    });
  }

  deleteLabel(labelId: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/labels/${labelId}`);
  }

  /**
   * Create a clause type. The backend slugifies the label into the immutable
   * machine `value`; on collision it silently appends a numeric suffix.
   */
  createClauseType(label: string): Observable<ClauseTypeOption> {
    return this.http.post<ClauseTypeOption>(`${this.base}/clause-types`, { label });
  }

  /** Update a clause type's display label; the machine `value` is immutable. */
  updateClauseType(id: number, label: string): Observable<ClauseTypeOption> {
    return this.http.patch<ClauseTypeOption>(`${this.base}/clause-types/${id}`, { label });
  }

  /** Delete a clause type; cascades to every label referencing it. */
  deleteClauseType(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/clause-types/${id}`);
  }
}
