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
import { RouterLink } from '@angular/router';
import { Subject, debounceTime } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { clauseTypeColor } from '../../core/clause-type-color';
import type {
  ClauseType,
  ClauseTypeOption,
  DocumentGroup,
  DocumentSummary,
  GroupedDocuments,
} from '../../core/models';

interface ViewState {
  loading: boolean;
  flat: DocumentSummary[];
  groups: DocumentGroup[] | null;
  error: string | null;
}

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
    RouterLink,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  private readonly api = inject(ApiService);

  readonly clauseTypes = signal<ClauseTypeOption[]>([]);
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
    this.api
      .listClauseTypes()
      .pipe(takeUntilDestroyed())
      .subscribe((opts) => this.clauseTypes.set(opts));

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

  colorFor(type: ClauseType): { bg: string; fg: string } {
    return clauseTypeColor(type);
  }

  labelFor(type: ClauseType): string {
    return this.clauseTypes().find((c) => c.value === type)?.label ?? type;
  }

  private refresh(): void {
    this.state.update((s) => ({ ...s, loading: true, error: null }));
    this.api
      .listDocuments({
        q: this.query().trim() || undefined,
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
