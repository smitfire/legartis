import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';

import { ApiService } from './api.service';

describe('ApiService — clause type CRUD', () => {
  let api: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts the label and returns the created clause type', () => {
    let received: { id: number; value: string; label: string } | undefined;
    api.createClauseType('Service Level Agreement').subscribe((opt) => (received = opt));

    const req = httpMock.expectOne('/api/clause-types');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ label: 'Service Level Agreement' });
    req.flush({ id: 8, value: 'service_level_agreement', label: 'Service Level Agreement' });

    expect(received).toEqual({
      id: 8,
      value: 'service_level_agreement',
      label: 'Service Level Agreement',
    });
  });

  it('patches the label without changing the value', () => {
    let received: { id: number; value: string; label: string } | undefined;
    api.updateClauseType(8, 'Service Level Agreement v2').subscribe((opt) => (received = opt));

    const req = httpMock.expectOne('/api/clause-types/8');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ label: 'Service Level Agreement v2' });
    req.flush({ id: 8, value: 'service_level_agreement', label: 'Service Level Agreement v2' });

    expect(received?.label).toBe('Service Level Agreement v2');
    expect(received?.value).toBe('service_level_agreement');
  });

  it('deletes a clause type by id', () => {
    let completed = false;
    api.deleteClauseType(8).subscribe({ complete: () => (completed = true) });

    const req = httpMock.expectOne('/api/clause-types/8');
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });

    expect(completed).toBe(true);
  });
});
