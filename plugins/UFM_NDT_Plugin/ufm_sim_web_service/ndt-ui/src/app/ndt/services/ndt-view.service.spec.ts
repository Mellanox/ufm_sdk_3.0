import { TestBed } from '@angular/core/testing';

import { NdtViewService } from './ndt-view.service';

describe('NdtViewService', () => {
  let service: NdtViewService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(NdtViewService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
