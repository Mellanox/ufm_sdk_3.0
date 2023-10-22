import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CablesValidationReportModalComponent } from './cables-validation-report-modal.component';

describe('CablesValidationReportModalComponent', () => {
  let component: CablesValidationReportModalComponent;
  let fixture: ComponentFixture<CablesValidationReportModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CablesValidationReportModalComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CablesValidationReportModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
