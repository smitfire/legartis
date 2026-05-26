import { CommonModule, DatePipe } from '@angular/common';
import { Component, effect, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { ClauseTypeColorPipe } from '../../core/clause-type-color.pipe';
import type { ClauseType, ClauseTypeOption, DocumentDetail } from '../../core/models';

/**
 * Document detail view: renders every sentence with its labels, lets a user
 * add/remove labels per sentence, and refetches in place so the rendered
 * order stays stable. Wired to the `:id` route param via component input
 * binding.
 */
@Component({
  selector: 'app-document-detail',
  imports: [
    CommonModule,
    DatePipe,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    RouterLink,
    ClauseTypeColorPipe,
  ],
  templateUrl: './document-detail.component.html',
  styleUrl: './document-detail.component.scss',
})
export class DocumentDetailComponent {
  /** Document id bound from the `:id` route param (via `withComponentInputBinding()`). */
  readonly id = input.required<string>();

  private readonly api = inject(ApiService);
  private readonly snackBar = inject(MatSnackBar);

  readonly clauseTypes = signal<ClauseTypeOption[]>([]);
  readonly document = signal<DocumentDetail | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly pendingSentence = signal<number | null>(null);

  constructor() {
    this.api.listClauseTypes().subscribe((opts) => this.clauseTypes.set(opts));

    effect(() => {
      const id = this.id();
      if (id) this.load();
    });
  }

  labelFor(type: ClauseType): string {
    return this.clauseTypes().find((c) => c.value === type)?.label ?? type;
  }

  availableTypesFor(sentenceId: number): ClauseTypeOption[] {
    const doc = this.document();
    if (!doc) return [];
    const sentence = doc.sentences.find((s) => s.id === sentenceId);
    const taken = new Set((sentence?.labels ?? []).map((l) => l.clause_type));
    return this.clauseTypes().filter((c) => !taken.has(c.value));
  }

  addLabel(sentenceId: number, type: ClauseType): void {
    this.pendingSentence.set(sentenceId);
    this.api.createLabel(sentenceId, type).subscribe({
      next: () => {
        this.pendingSentence.set(null);
        this.load(true);
      },
      error: (err) => {
        this.pendingSentence.set(null);
        const detail =
          err?.error?.detail ??
          (err?.status === 409 ? 'Sentence already has this label' : 'Failed to add label');
        this.snackBar.open(detail, 'Dismiss', { duration: 4000 });
      },
    });
  }

  removeLabel(labelId: number): void {
    this.api.deleteLabel(labelId).subscribe({
      next: () => this.load(true),
      error: () => this.snackBar.open('Failed to remove label', 'Dismiss', { duration: 4000 }),
    });
  }

  private load(silent = false): void {
    if (!silent) this.loading.set(true);
    this.api.getDocument(Number(this.id())).subscribe({
      next: (doc) => {
        this.document.set(doc);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.status === 404 ? 'Contract not found' : 'Failed to load contract');
      },
    });
  }
}
