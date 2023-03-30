import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubnetMergerViewComponent } from './subnet-merger-view.component';

describe('SubnetMergerViewComponent', () => {
  let component: SubnetMergerViewComponent;
  let fixture: ComponentFixture<SubnetMergerViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SubnetMergerViewComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SubnetMergerViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
