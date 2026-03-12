import { TestBed } from '@angular/core/testing';

import { HabitsService } from './habits';

describe('HabitsService', () => {
  let service: HabitsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(HabitsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
