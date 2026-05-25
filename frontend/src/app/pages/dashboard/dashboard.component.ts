import { Component } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';

@Component({
  selector: 'app-dashboard',
  imports: [MatToolbarModule],
  template: `
    <mat-toolbar color="primary">Legartis · Contract Clause Tracker</mat-toolbar>
    <main class="page">
      <p>Scaffold ready — dashboard arrives in Phase 5.</p>
    </main>
  `,
  styles: `
    .page {
      padding: 1.5rem;
    }
  `,
})
export class DashboardComponent {}
