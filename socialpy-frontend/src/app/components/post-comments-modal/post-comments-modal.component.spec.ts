import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PostCommentsModalComponent } from './post-comments-modal.component';

describe('PostCommentsModalComponent', () => {
  let component: PostCommentsModalComponent;
  let fixture: ComponentFixture<PostCommentsModalComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PostCommentsModalComponent]
    });
    fixture = TestBed.createComponent(PostCommentsModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
