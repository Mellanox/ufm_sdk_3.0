import { TestBed } from '@angular/core/testing';

import { CableValidationBackendService } from './cable-validation-backend.service';

describe('CableValidationBackendService', () => {
  let service: CableValidationBackendService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CableValidationBackendService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
