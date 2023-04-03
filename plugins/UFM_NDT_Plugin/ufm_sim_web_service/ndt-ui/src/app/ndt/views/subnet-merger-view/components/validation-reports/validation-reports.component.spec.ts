import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ValidationReportsComponent } from './validation-reports.component';

describe('ValidationReportsComponent', () => {
  let component: ValidationReportsComponent;
  let fixture: ComponentFixture<ValidationReportsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ValidationReportsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ValidationReportsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
