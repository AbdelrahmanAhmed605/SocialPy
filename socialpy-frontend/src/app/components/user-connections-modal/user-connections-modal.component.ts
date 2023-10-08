import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import {
  ModalController,
  InfiniteScrollCustomEvent,
  ToastController,
} from '@ionic/angular';

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
    private modalCtrl: ModalController,
    private toastCtrl: ToastController
  ) {}

  // Contains a list of connection users (either followers or following users)
  connectionUsers: any[] = [];
  loadingUsers: boolean = true; // Keep track if user connections data is currently being fetched
  currentConnectionsPage = 1; // keep track of the current page of user connections (for pagination)
  hasMoreConnectionsData: boolean = false; // Keeps track if there is more paginated data

  // Keeps track of the current username search filter applied by the user
  usernameSearchQuery!: string | undefined;

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
  // username argument is optional to filter the data to match the username only if provided
  async fetchUsers(username?: string) {
    this.loadingUsers = true;
    if (this.connectionType === 'followers') {
      this.followService
        .getUsersFollowers(this.userId, this.currentConnectionsPage, username)
        .pipe(takeUntil(this.destroyed$))
        .subscribe({
          next: (data: UserConnectionsResponse) => {
            this.hasMoreConnectionsData = !!data.next;
            // Append new paginated results to existing connections array
            this.connectionUsers = [...this.connectionUsers, ...data.results];
            this.loadingUsers = false;
          },
          error: (error) => {
            // Handle any errors here
            console.error('Error fetching followers:', error);
            this.loadingUsers = false;
          },
        });
    } else if (this.connectionType === 'following') {
      this.followService
        .getUsersFollowing(this.userId, this.currentConnectionsPage)
        .pipe(takeUntil(this.destroyed$))
        .subscribe({
          next: (data: UserConnectionsResponse) => {
            this.hasMoreConnectionsData = !!data.next;
            // Append new paginated results to existing connections array
            this.connectionUsers = [...this.connectionUsers, ...data.results];
            this.loadingUsers = false;
          },
          error: (error) => {
            // Handle any errors here
            console.error('Error fetching followers:', error);
            this.loadingUsers = false;
          },
        });
    }
  }

  // Infinite scrolling event to call the next page of paginated results
  loadMoreConnections(event: Event) {
    // Increment the current page of paginated user connections data
    this.currentConnectionsPage++;

    // Call the service api with the updated page parameter
    if (
      this.usernameSearchQuery === null ||
      this.usernameSearchQuery === undefined
    ) {
      this.fetchUsers();
    } else {
      this.fetchUsers(this.usernameSearchQuery);
    }

    setTimeout(() => {
      // Complete the infinite scroll event to indicate that loading is done
      (event as InfiniteScrollCustomEvent).target.complete();
      // Scroll back to the previous position
    }, 500);
  }

  // Handles user input in ionic searchbar for searching usernames and updates the user list accordingly.
  searchUsername(event: Event) {
    if (event && event.target) {
      // Get the lowercase username query from the input field
      const usernameQuery = (
        event.target as HTMLInputElement
      ).value.toLowerCase();

      if (usernameQuery === '' || usernameQuery === null) {
        // Clear the username filter if the query is empty
        this.usernameSearchQuery = undefined;
      } else {
        // Set the username filter to the query if it exists
        this.usernameSearchQuery = usernameQuery;
      }

      // Reset state variables and fetch users based on the updated username filter
      this.resetAndFetchUsers(this.usernameSearchQuery);
    }
  }

  // Resets data and pagination states and fetches user connections.
  // If 'usernameQuery' is provided, it filters results; otherwise, it retrieves the original list.
  resetAndFetchUsers(usernameQuery?: string) {
    this.currentConnectionsPage = 1;
    this.hasMoreConnectionsData = false;
    this.loadingUsers = true;
    this.connectionUsers = [];

    // Fetch user connections with the optional username filter if it exists
    this.fetchUsers(usernameQuery);
  }

  // Function to follow a user with a specified id
  followUser(userId: number) {
    // Call the service API function to follow the user
    this.followService
      .followUser(userId)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: (response) => {
          if (response && response.follow_status) {
            // Find the index of the user in the connectionUsers array
            const userIndex = this.connectionUsers.findIndex(
              (user) => user.id === userId
            );
            if (userIndex !== -1) {
              // Update the requesting_user_follow_status based on the API response to update the UI
              this.connectionUsers[userIndex].requesting_user_follow_status =
                response.follow_status;
            } else {
              console.error(
                'An error occurred while processing your request. Please try again later.'
              );
              // Display a toast message to alert the user an error occured
              this.followUserErrorToast();
            }
          }
        },
        error: (error) => {
          console.error('Error following user:', error);
          // Display a toast message to alert the user an error occured
          this.followUserErrorToast();
        },
      });
  }

  // Display an error ionic toast at the top of the page to alert the user if an error occured following a user
  async followUserErrorToast() {
    const toast = await this.toastCtrl.create({
      message: 'Error following user',
      duration: 1500,
      position: 'top',
    });

    await toast.present();
  }

  // Function to unfollow a user with a specified id
  unfollowUser(userId: number) {
    // Call the service API function to unfollow the user
    this.followService
      .unfollowUser(userId)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: (response) => {
          if (response) {
            // Find the index of the specified user in the connectionUsers array
            const userIndex = this.connectionUsers.findIndex(
              (user) => user.id === userId
            );
            if (userIndex !== -1) {
              // Update the requesting_user_follow_status based on the API response to update the UI
              this.connectionUsers[userIndex].requesting_user_follow_status =
                response.follow_status;
            } else {
              console.error(
                'An error occurred while processing your request. Please try again later.'
              );
              // Display a toast message to alert the user an error occured
              this.unfollowUserErrorToast();
            }
          }
        },
        error: (error) => {
          console.error('Error unfollowing user:', error);
          // Display a toast message to alert the user an error occured
          this.unfollowUserErrorToast();
        },
      });
  }

  // Display an error ionic toast at the top of the page to alert the user if an error occured unfollowing a user
  async unfollowUserErrorToast() {
    const toast = await this.toastCtrl.create({
      message: 'Error unfollowing user',
      duration: 1500,
      position: 'top',
    });

    await toast.present();
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
