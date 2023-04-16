import { TestBed } from '@angular/core/testing';

import { UfmDevicesDataTableHookService } from './ufm-devices-data-table-hook.service';

describe('UfmDevicesDataTableHookService', () => {
  let service: UfmDevicesDataTableHookService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(UfmDevicesDataTableHookService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
