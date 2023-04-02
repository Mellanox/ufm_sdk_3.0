import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NdtFilesViewComponent } from './ndt-files-view.component';

describe('NdtFilesViewComponent', () => {
  let component: NdtFilesViewComponent;
  let fixture: ComponentFixture<NdtFilesViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NdtFilesViewComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NdtFilesViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
