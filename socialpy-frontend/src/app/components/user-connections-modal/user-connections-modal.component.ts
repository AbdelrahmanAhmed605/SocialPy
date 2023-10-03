import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { ModalController } from '@ionic/angular';

import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { UserConnectionsResponse } from 'src/app/interface-types/user-connections.model';

import { FollowService } from 'src/app/api-services/follow/follow.service';

import { faUser, faXmark } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-user-connections-modal',
  templateUrl: './user-connections-modal.component.html',
  styleUrls: ['./user-connections-modal.component.css'],
})
export class UserConnectionsModalComponent implements OnInit, OnDestroy {
  @Input() userId!: number; // Input property to receive the ID of the user from the parent component
  @Input() connectionType!: string; // string indicating whether the connections list is "followers" or "following"
  constructor(
    private router: Router,
    private followService: FollowService,
    private modalCtrl: ModalController
  ) {}

  // Contains a list of connection users (either followers or following users)
  connectionUsers: any[] = [];

  private destroyed$ = new Subject<void>(); // Subject to track component destruction for subscription cleanup

  // Font Awesome icons
  faXmark = faXmark;
  faUser = faUser;

  ngOnInit() {
    // Fetch the list of user connections when the modal component is initialized
    this.fetchUsers();
  }

  // Call the service api function to retrieve the list of users based on the connectionType
  // The connectionType lets us know if we should fetch the users followers or following
  async fetchUsers() {
    if (this.connectionType === 'followers') {
      this.followService
        .getUsersFollowers(this.userId)
        .pipe(takeUntil(this.destroyed$))
        .subscribe({
          next: (data: UserConnectionsResponse) => {
            this.connectionUsers = data.results;
          },
          error: (error) => {
            // Handle any errors here
            console.error('Error fetching followers:', error);
          },
        });
    } else if (this.connectionType === 'following') {
      this.followService
        .getUsersFollowing(this.userId)
        .pipe(takeUntil(this.destroyed$))
        .subscribe({
          next: (data: UserConnectionsResponse) => {
            this.connectionUsers = data.results;
          },
          error: (error) => {
            // Handle any errors here
            console.error('Error fetching followers:', error);
          },
        });
    }
  }

  // Function to close the modal display
  closeModal() {
    this.modalCtrl.dismiss();
  }

  // Redirect the user to the profile page associated with the user they are attempting to view
  goToUserProfilePage(userId: string) {
    this.closeModal();

    // Navigate to the same route with refresh
    this.router.navigate(['/profile', userId]);
  }

  ngOnDestroy(): void {
    // Complete the `destroyed$` Subject to signal unsubscription to any ongoing observables
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
