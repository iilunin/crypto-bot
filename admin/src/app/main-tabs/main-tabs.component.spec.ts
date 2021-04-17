import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MainTabsComponent } from './main-tabs.component';

describe('MainTabsComponent', () => {
  let component: MainTabsComponent;
  let fixture: ComponentFixture<MainTabsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MainTabsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MainTabsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
