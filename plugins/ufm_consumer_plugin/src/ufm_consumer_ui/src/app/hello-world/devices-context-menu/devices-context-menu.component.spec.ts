import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DevicesContextMenuComponent } from './devices-context-menu.component';

describe('DevicesContextMenuComponent', () => {
  let component: DevicesContextMenuComponent;
  let fixture: ComponentFixture<DevicesContextMenuComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DevicesContextMenuComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DevicesContextMenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
