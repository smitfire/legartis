import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./pages/home/home.component').then((m) => m.HomeComponent),
  },
  {
    path: 'contracts',
    loadComponent: () =>
      import('./pages/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'clause-types',
    loadComponent: () =>
      import('./pages/clause-types/clause-types.component').then((m) => m.ClauseTypesComponent),
  },
  {
    path: 'upload',
    loadComponent: () => import('./pages/upload/upload.component').then((m) => m.UploadComponent),
  },
  {
    path: 'documents/:id',
    loadComponent: () =>
      import('./pages/document-detail/document-detail.component').then(
        (m) => m.DocumentDetailComponent,
      ),
  },
];
