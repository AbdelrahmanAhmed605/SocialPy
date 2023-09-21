import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PostLikersModalComponent } from './post-likers-modal.component';

describe('PostLikersModalComponent', () => {
  let component: PostLikersModalComponent;
  let fixture: ComponentFixture<PostLikersModalComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PostLikersModalComponent]
    });
    fixture = TestBed.createComponent(PostLikersModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
