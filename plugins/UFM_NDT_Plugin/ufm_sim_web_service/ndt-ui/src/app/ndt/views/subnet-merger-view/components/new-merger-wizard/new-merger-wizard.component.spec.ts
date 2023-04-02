import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NewMergerWizardComponent } from './new-merger-wizard.component';

describe('NewMergerWizardComponent', () => {
  let component: NewMergerWizardComponent;
  let fixture: ComponentFixture<NewMergerWizardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NewMergerWizardComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NewMergerWizardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
