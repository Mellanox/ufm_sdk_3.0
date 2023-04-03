import { TestBed } from '@angular/core/testing';

import { SubnetMergerBackendService } from './subnet-merger-backend.service';

describe('SubnetMergerBackendService', () => {
  let service: SubnetMergerBackendService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SubnetMergerBackendService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
