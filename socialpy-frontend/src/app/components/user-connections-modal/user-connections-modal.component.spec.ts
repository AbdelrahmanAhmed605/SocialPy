import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserConnectionsModalComponent } from './user-connections-modal.component';

describe('UserConnectionsModalComponent', () => {
  let component: UserConnectionsModalComponent;
  let fixture: ComponentFixture<UserConnectionsModalComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [UserConnectionsModalComponent]
    });
    fixture = TestBed.createComponent(UserConnectionsModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
