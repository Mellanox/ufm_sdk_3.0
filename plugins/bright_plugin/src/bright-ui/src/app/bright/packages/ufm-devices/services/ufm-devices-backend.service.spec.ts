import { TestBed } from '@angular/core/testing';

import { UfmDevicesBackendService } from './ufm-devices-backend.service';

describe('UfmDevicesBackendService', () => {
  let service: UfmDevicesBackendService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(UfmDevicesBackendService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
