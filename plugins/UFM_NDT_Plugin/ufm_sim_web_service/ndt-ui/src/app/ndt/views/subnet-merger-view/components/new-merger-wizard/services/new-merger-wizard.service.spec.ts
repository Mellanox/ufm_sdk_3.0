import { TestBed } from '@angular/core/testing';

import { NewMergerWizardService } from './new-merger-wizard.service';

describe('NewMergerWizardService', () => {
  let service: NewMergerWizardService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(NewMergerWizardService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
