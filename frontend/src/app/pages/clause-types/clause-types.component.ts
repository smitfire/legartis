import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { ApiService } from '../../core/api.service';
import { clauseTypeColor } from '../../core/clause-type-color';
import type { ClauseTypeOption } from '../../core/models';

interface ViewState {
  loading: boolean;
  items: ClauseTypeOption[];
  error: string | null;
}

interface EditingState {
  id: number;
  label: string;
}

@Component({
  selector: 'app-clause-types',
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './clause-types.component.html',
  styleUrl: './clause-types.component.scss',
})
export class ClauseTypesComponent {
  private readonly api = inject(ApiService);
  private readonly snackBar = inject(MatSnackBar);

  readonly state = signal<ViewState>({ loading: true, items: [], error: null });
  readonly newLabel = signal('');
  readonly creating = signal(false);
  readonly pendingId = signal<number | null>(null);
  readonly editing = signal<EditingState | null>(null);

  readonly canSubmit = computed(() => this.newLabel().trim().length > 0);
  readonly editingId = computed(() => this.editing()?.id ?? null);

  constructor() {
    this.refresh();
  }

  colorFor(value: string): { bg: string; fg: string } {
    return clauseTypeColor(value);
  }

  startEditing(option: ClauseTypeOption): void {
    this.editing.set({ id: option.id, label: option.label });
  }

  cancelEditing(): void {
    this.editing.set(null);
  }

  updateEditingLabel(label: string): void {
    this.editing.update((current) => (current ? { ...current, label } : current));
  }

  saveEdit(id: number): void {
    const editing = this.editing();
    const label = editing?.label.trim() ?? '';
    if (label.length === 0) return;
    this.pendingId.set(id);
    this.api.updateClauseType(id, label).subscribe({
      next: () => {
        this.pendingId.set(null);
        this.editing.set(null);
        this.refresh();
      },
      error: (err) => this.handleError(err, 'Failed to update clause type'),
    });
  }

  create(): void {
    const label = this.newLabel().trim();
    if (label.length === 0) return;
    this.creating.set(true);
    this.api.createClauseType(label).subscribe({
      next: () => {
        this.creating.set(false);
        this.newLabel.set('');
        this.refresh();
      },
      error: (err) => this.handleError(err, 'Failed to create clause type'),
    });
  }

  delete(option: ClauseTypeOption): void {
    this.pendingId.set(option.id);
    this.api.deleteClauseType(option.id).subscribe({
      next: () => {
        this.pendingId.set(null);
        this.snackBar.open(`Deleted “${option.label}”`, undefined, { duration: 3000 });
        this.refresh();
      },
      error: (err) => this.handleError(err, 'Failed to delete clause type'),
    });
  }

  private refresh(): void {
    this.state.update((s) => ({ ...s, loading: true, error: null }));
    this.api.listClauseTypes().subscribe({
      next: (items) => this.state.set({ loading: false, items, error: null }),
      error: (err) =>
        this.state.set({
          loading: false,
          items: [],
          error: err?.message ?? 'Failed to load clause types',
        }),
    });
  }

  private handleError(err: unknown, fallback: string): void {
    this.creating.set(false);
    this.pendingId.set(null);
    // HttpErrorResponse buries FastAPI's actionable `detail` field under
    // `err.error`; the top-level `message` is the framework's generic
    // "Http failure response for /api/..." string. Surface the backend
    // reason first so the user sees what actually went wrong.
    const httpError = err as { error?: { detail?: string }; message?: string };
    const message = httpError?.error?.detail ?? httpError?.message ?? fallback;
    this.snackBar.open(message, 'Dismiss', { duration: 5000 });
  }
}
