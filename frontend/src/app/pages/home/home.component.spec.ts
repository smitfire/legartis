import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { HomeComponent } from './home.component';

describe('HomeComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HomeComponent],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('renders two routerLink tiles pointing to /contracts and /clause-types', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();

    const links = (fixture.nativeElement as HTMLElement).querySelectorAll(
      'a[routerLink]',
    );
    const targets = Array.from(links).map((a) => a.getAttribute('routerLink'));
    expect(targets).toContain('/contracts');
    expect(targets).toContain('/clause-types');
  });
});
