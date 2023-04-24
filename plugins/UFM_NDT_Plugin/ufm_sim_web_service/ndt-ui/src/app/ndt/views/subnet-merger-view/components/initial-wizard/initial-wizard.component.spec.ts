import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InitialWizardComponent } from './initial-wizard.component';

describe('InitialWizardComponent', () => {
  let component: InitialWizardComponent;
  let fixture: ComponentFixture<InitialWizardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ InitialWizardComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InitialWizardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
