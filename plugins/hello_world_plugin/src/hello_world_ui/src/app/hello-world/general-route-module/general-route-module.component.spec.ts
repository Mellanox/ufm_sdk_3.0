import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GeneralRouteModuleComponent } from './general-route-module.component';

describe('GeneralRouteModuleComponent', () => {
  let component: GeneralRouteModuleComponent;
  let fixture: ComponentFixture<GeneralRouteModuleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ GeneralRouteModuleComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(GeneralRouteModuleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
