import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { DashboardComponent } from './dashboard.component';

describe('DashboardComponent — chip-row navigation', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('renders a Manage link that routes to /clause-types from the chip row', () => {
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();

    // Drain the initial HTTP calls so afterEach.verify() stays happy.
    const httpMock = TestBed.inject(HttpTestingController);
    httpMock.expectOne((req) => req.url.startsWith('/api/clause-type-counts')).flush([]);
    httpMock.expectOne((req) => req.url.startsWith('/api/documents')).flush([]);
    fixture.detectChanges();

    const manageLink = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-test="manage-clause-types-link"]',
    );
    expect(manageLink?.getAttribute('routerLink')).toBe('/clause-types');
  });
});
