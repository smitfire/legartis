import { CommonModule, DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule, type MatChipListboxChange } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterLink } from '@angular/router';
import { Subject, debounceTime } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { ClauseTypeColorPipe } from '../../core/clause-type-color.pipe';
import type {
  ClauseType,
  ClauseTypeCount,
  DocumentGroup,
  DocumentSummary,
  GroupedDocuments,
} from '../../core/models';

/**
 * Single-signal view model for the dashboard list. Exactly one of `flat` or
 * `groups` is populated per render — `groups` is non-null only when grouping
 * by clause type is enabled.
 */
interface ViewState {
  loading: boolean;
  flat: DocumentSummary[];
  groups: DocumentGroup[] | null;
  error: string | null;
}

/**
 * Dashboard view: search, clause-type filter chips, and optional grouping by
 * clause type. All filtering happens server-side; this component only owns
 * input state and renders whatever `/api/documents` returns.
 */
@Component({
  selector: 'app-dashboard',
  imports: [
    CommonModule,
    FormsModule,
    DatePipe,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
    MatTooltipModule,
    RouterLink,
    ClauseTypeColorPipe,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  private readonly api = inject(ApiService);

  readonly clauseTypes = signal<ClauseTypeCount[]>([]);
  readonly selectedTypes = signal<Set<ClauseType>>(new Set());
  readonly query = signal('');
  readonly groupByType = signal(false);
  readonly state = signal<ViewState>({
    loading: true,
    flat: [],
    groups: null,
    error: null,
  });

  readonly hasActiveFilters = computed(
    () => this.query() !== '' || this.selectedTypes().size > 0 || this.groupByType(),
  );

  readonly selectedTypesValue = computed(() => Array.from(this.selectedTypes()));

  private readonly queryInput$ = new Subject<string>();

  constructor() {
    this.queryInput$
      .pipe(debounceTime(200), takeUntilDestroyed())
      .subscribe((value) => {
        this.query.set(value);
        this.refresh();
      });

    this.refresh();
  }

  onQueryInput(value: string): void {
    this.queryInput$.next(value);
  }

  onTypesChange(event: MatChipListboxChange): void {
    this.selectedTypes.set(new Set(event.value as ClauseType[]));
    this.refresh();
  }

  toggleGroupByType(enabled: boolean): void {
    this.groupByType.set(enabled);
    this.refresh();
  }

  clearFilters(): void {
    this.query.set('');
    this.selectedTypes.set(new Set());
    this.groupByType.set(false);
    this.refresh();
  }

  labelFor(type: ClauseType): string {
    return this.clauseTypes().find((c) => c.value === type)?.label ?? type;
  }

  /**
   * Refetches counts and the document list together. Chip counts intentionally
   * reflect the current search query (not selected types) so users never click
   * a filter that would yield zero results in the visible set.
   */
  private refresh(): void {
    const q = this.query().trim() || undefined;
    this.state.update((s) => ({ ...s, loading: true, error: null }));

    this.api.listClauseTypeCounts(q).subscribe((counts) => this.clauseTypes.set(counts));

    this.api
      .listDocuments({
        q,
        types: this.selectedTypes().size > 0 ? Array.from(this.selectedTypes()) : undefined,
        groupBy: this.groupByType() ? 'type' : undefined,
      })
      .subscribe({
        next: (result) => {
          if ('groups' in (result as GroupedDocuments)) {
            this.state.set({
              loading: false,
              flat: [],
              groups: (result as GroupedDocuments).groups,
              error: null,
            });
          } else {
            this.state.set({
              loading: false,
              flat: result as DocumentSummary[],
              groups: null,
              error: null,
            });
          }
        },
        error: (err) =>
          this.state.set({
            loading: false,
            flat: [],
            groups: null,
            error: err?.message ?? 'Failed to load documents',
          }),
      });
  }
}
