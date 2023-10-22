import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CableValidationTableComponent } from './cable-validation-table.component';

describe('CableValidationTableComponent', () => {
  let component: CableValidationTableComponent;
  let fixture: ComponentFixture<CableValidationTableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CableValidationTableComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CableValidationTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
