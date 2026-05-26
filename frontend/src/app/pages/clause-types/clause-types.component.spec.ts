import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { ClauseTypesComponent } from './clause-types.component';

const SAMPLE_TYPES = [
  { id: 1, value: 'limitation_of_liability', label: 'Limitation of Liability' },
  { id: 2, value: 'confidentiality', label: 'Confidentiality' },
];

describe('ClauseTypesComponent', () => {
  let fixture: ComponentFixture<ClauseTypesComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ClauseTypesComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ClauseTypesComponent);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  function answerInitialList(): void {
    fixture.detectChanges();
    httpMock.expectOne('/api/clause-types').flush(SAMPLE_TYPES);
    fixture.detectChanges();
  }

  it('renders one row per clause type returned by the API', () => {
    answerInitialList();

    const labels = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('[data-test="clause-type-label"]'),
    ).map((el) => el.textContent?.trim());
    expect(labels).toEqual(['Limitation of Liability', 'Confidentiality']);
  });

  it('posts a new clause type when the create form is submitted and refetches', () => {
    answerInitialList();

    const component = fixture.componentInstance;
    component.newLabel.set('Force Majeure');
    fixture.detectChanges();
    component.create();
    fixture.detectChanges();

    const created = httpMock.expectOne('/api/clause-types');
    expect(created.request.method).toBe('POST');
    expect(created.request.body).toEqual({ label: 'Force Majeure' });
    created.flush({ id: 3, value: 'force_majeure', label: 'Force Majeure' });

    const refresh = httpMock.expectOne('/api/clause-types');
    refresh.flush([...SAMPLE_TYPES, { id: 3, value: 'force_majeure', label: 'Force Majeure' }]);
  });

  it('deletes a clause type when the delete button is clicked', () => {
    answerInitialList();

    const deleteButton = fixture.nativeElement.querySelector(
      '[data-test="delete-clause-type-1"]',
    ) as HTMLButtonElement;
    deleteButton.click();
    fixture.detectChanges();

    const del = httpMock.expectOne('/api/clause-types/1');
    expect(del.request.method).toBe('DELETE');
    del.flush(null, { status: 204, statusText: 'No Content' });

    httpMock.expectOne('/api/clause-types').flush([SAMPLE_TYPES[1]]);
  });
});
