import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Router } from '@angular/router';

import { ApiService } from '../../core/api.service';

@Component({
  selector: 'app-upload',
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.scss',
})
export class UploadComponent {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);

  readonly file = signal<File | null>(null);
  readonly uploading = signal(false);
  readonly dragOver = signal(false);
  readonly error = signal<string | null>(null);

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(false);
    const dropped = event.dataTransfer?.files?.[0] ?? null;
    if (dropped) this.selectFile(dropped);
  }

  onFilePicked(event: Event): void {
    const input = event.target as HTMLInputElement;
    const picked = input.files?.[0] ?? null;
    if (picked) this.selectFile(picked);
  }

  clearFile(): void {
    this.file.set(null);
    this.error.set(null);
  }

  upload(): void {
    const file = this.file();
    if (!file) return;
    this.uploading.set(true);
    this.error.set(null);

    this.api.uploadDocument(file).subscribe({
        next: (doc) => {
          this.uploading.set(false);
          this.snackBar.open(`Uploaded ${doc.title} — ${doc.sentences.length} sentences`, 'OK', {
            duration: 4000,
          });
          this.router.navigate(['/documents', doc.id]);
        },
        error: (err) => {
          this.uploading.set(false);
          const detail =
            err?.error?.detail ??
            (typeof err?.error === 'string' ? err.error : null) ??
            err?.message ??
            'Upload failed';
          this.error.set(detail);
          this.snackBar.open(`Upload failed: ${detail}`, 'Dismiss', { duration: 6000 });
        },
      });
  }

  private selectFile(file: File): void {
    const allowed = ['.txt', '.md', '.markdown'];
    const lower = file.name.toLowerCase();
    if (!allowed.some((ext) => lower.endsWith(ext))) {
      this.snackBar.open(
        `Only plain text or markdown files are supported (got ${file.name}).`,
        'OK',
        { duration: 5000 },
      );
      return;
    }
    this.file.set(file);
    this.error.set(null);
  }
}
