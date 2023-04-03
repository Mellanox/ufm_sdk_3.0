import { TestBed } from '@angular/core/testing';

import { SubnetMergerViewService } from './subnet-merger-view.service';

describe('SubnetMergerViewService', () => {
  let service: SubnetMergerViewService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SubnetMergerViewService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
