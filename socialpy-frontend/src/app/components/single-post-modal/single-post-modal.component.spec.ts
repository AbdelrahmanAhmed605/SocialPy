import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SinglePostModalComponent } from './single-post-modal.component';

describe('SinglePostModalComponent', () => {
  let component: SinglePostModalComponent;
  let fixture: ComponentFixture<SinglePostModalComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [SinglePostModalComponent]
    });
    fixture = TestBed.createComponent(SinglePostModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
