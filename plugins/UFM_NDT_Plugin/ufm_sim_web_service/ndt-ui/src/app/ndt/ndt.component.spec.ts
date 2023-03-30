import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NdtComponent } from './ndt.component';

describe('NdtComponent', () => {
  let component: NdtComponent;
  let fixture: ComponentFixture<NdtComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NdtComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NdtComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
