import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UploadNdtAndValidateComponent } from './upload-ndt-and-validate.component';

describe('UploadNdtAndValidateComponent', () => {
  let component: UploadNdtAndValidateComponent;
  let fixture: ComponentFixture<UploadNdtAndValidateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ UploadNdtAndValidateComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(UploadNdtAndValidateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
