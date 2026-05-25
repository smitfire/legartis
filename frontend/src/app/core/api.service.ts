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

export interface DashboardFilters {
  q?: string;
  types?: ClauseType[];
  groupBy?: 'type';
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api';

  listClauseTypes(): Observable<ClauseTypeOption[]> {
    return this.http.get<ClauseTypeOption[]>(`${this.base}/clause-types`);
  }

  listClauseTypeCounts(q?: string): Observable<ClauseTypeCount[]> {
    let params = new HttpParams();
    if (q) params = params.set('q', q);
    return this.http.get<ClauseTypeCount[]>(`${this.base}/clause-type-counts`, { params });
  }

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

  uploadDocument(file: File): Observable<DocumentDetail> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    return this.http.post<DocumentDetail>(`${this.base}/documents`, formData);
  }

  createLabel(sentenceId: number, clauseType: ClauseType): Observable<Label> {
    return this.http.post<Label>(`${this.base}/sentences/${sentenceId}/labels`, {
      clause_type: clauseType,
    });
  }

  deleteLabel(labelId: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/labels/${labelId}`);
  }
}
