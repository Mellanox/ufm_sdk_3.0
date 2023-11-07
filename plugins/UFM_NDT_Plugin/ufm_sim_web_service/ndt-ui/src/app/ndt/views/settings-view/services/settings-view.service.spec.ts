import { TestBed } from '@angular/core/testing';

import { SettingsViewService } from './settings-view.service';

describe('SettingsViewService', () => {
  let service: SettingsViewService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SettingsViewService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
