import { TestBed } from '@angular/core/testing';

import { InitialWizardService } from './initial-wizard.service';

describe('InitialWizardService', () => {
  let service: InitialWizardService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(InitialWizardService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
