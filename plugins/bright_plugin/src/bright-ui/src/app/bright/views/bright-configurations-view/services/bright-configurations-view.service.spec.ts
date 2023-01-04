import { TestBed } from '@angular/core/testing';

import { BrightConfigurationsViewService } from './bright-configurations-view.service';

describe('BrightConfigurationsViewService', () => {
  let service: BrightConfigurationsViewService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(BrightConfigurationsViewService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
