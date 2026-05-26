import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';

import { ApiService } from '../../core/api.service';
import { clauseTypeColor } from '../../core/clause-type-color';
import type { ClauseTypeOption } from '../../core/models';

interface ViewState {
  loading: boolean;
  items: ClauseTypeOption[];
  error: string | null;
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
  ],
  templateUrl: './clause-types.component.html',
  styleUrl: './clause-types.component.scss',
})
export class ClauseTypesComponent {
  private readonly api = inject(ApiService);
  private readonly snackBar = inject(MatSnackBar);

  readonly state = signal<ViewState>({ loading: true, items: [], error: null });
  readonly newLabel = signal('');
  readonly pendingId = signal<number | null>(null);
  readonly editingId = signal<number | null>(null);
  readonly editingLabel = signal('');

  readonly canSubmit = computed(() => this.newLabel().trim().length > 0);

  constructor() {
    this.refresh();
  }

  colorFor(value: string): { bg: string; fg: string } {
    return clauseTypeColor(value);
  }

  startEditing(option: ClauseTypeOption): void {
    this.editingId.set(option.id);
    this.editingLabel.set(option.label);
  }

  cancelEditing(): void {
    this.editingId.set(null);
    this.editingLabel.set('');
  }

  saveEdit(id: number): void {
    const label = this.editingLabel().trim();
    if (label.length === 0) return;
    this.pendingId.set(id);
    this.api.updateClauseType(id, label).subscribe({
      next: () => {
        this.pendingId.set(null);
        this.editingId.set(null);
        this.editingLabel.set('');
        this.refresh();
      },
      error: (err) => this.handleError(err, 'Failed to update clause type'),
    });
  }

  create(): void {
    const label = this.newLabel().trim();
    if (label.length === 0) return;
    this.pendingId.set(-1);
    this.api.createClauseType(label).subscribe({
      next: () => {
        this.pendingId.set(null);
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
      next: (items) =>
        this.state.set({ loading: false, items: items as ClauseTypeOption[], error: null }),
      error: (err) =>
        this.state.set({
          loading: false,
          items: [],
          error: err?.message ?? 'Failed to load clause types',
        }),
    });
  }

  private handleError(err: unknown, fallback: string): void {
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
