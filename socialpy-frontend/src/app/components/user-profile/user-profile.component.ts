import { Component, OnInit, HostListener, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import {
  ToastController,
  Platform,
  InfiniteScrollCustomEvent,
} from '@ionic/angular';

import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { UserService } from 'src/app/api-services/user/user.service';
import { FollowService } from 'src/app/api-services/follow/follow.service';

import { UserProfileResponse } from 'src/app/interface-types/user-profile.model';

import { faUser, faTableCells } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-user-profile',
  templateUrl: './user-profile.component.html',
  styleUrls: ['./user-profile.component.css'],
})
export class UserProfileComponent implements OnInit, OnDestroy {
  constructor(
    private activatedRoute: ActivatedRoute, // for retrieving route information.
    private userService: UserService, // for performing user-related api calls
    private followService: FollowService, // for performing follow-related api calls
    private toastCtrl: ToastController, // for displaying ionic toast notifications.
    private platform: Platform // service for detecting screen width
  ) {
    // Determine if the screen is considered large or small based on the initial platform width.
    this.isLargeScreen = this.platform.width() > 736;
  }

  // Font Awesome icons
  faUser = faUser;
  faTableCells = faTableCells;

  isLargeScreen!: boolean; // determines if the width of the device is large or small

  isSelectedTab: string = 'posts'; // checks which tab in the tablist is currently selected. The default is "posts"

  userId!: number; // Contains the id of the user being viewed in the component
  userData: UserProfileResponse | undefined; // Contains the user's profile data

  userDataError: any = null; // Tracks if any errors occur while fetching user profile data

  currentUserProfilePostsPage = 1; // keep track of the current page of user's profile posts (for pagination)
  hasMoreUserProfilePosts: boolean = false; // Keeps track if there is more paginated profile posts

  private destroyed$ = new Subject<void>(); // Subject to track component destruction for subscription cleanup

  ngOnInit() {
    // Get the userId from the route parameter
    this.activatedRoute.paramMap
      .pipe(takeUntil(this.destroyed$))
      .subscribe((params) => {
        const userIdParam = params.get('userId');
        if (userIdParam !== null) {
          this.userId = parseInt(userIdParam, 10);
          this.fetchUser(this.userId);
        } else {
          // Handle the case when 'userId' is null (not present in the params).
          this.userDataError = {
            message: 'User ID not found in route parameters',
            status: 404,
          };
        }
      });
  }

  // Update the 'isLargeScreen' property based on the platform's width
  @HostListener('window:resize', ['$event'])
  onResize(event: Event): void {
    this.isLargeScreen = this.platform.width() > 736;
  }

  // Call the service api function to retrieve user's profile data
  async fetchUser(userId: number) {
    this.userService
      .getUserProfile(userId, this.currentUserProfilePostsPage)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: (data: UserProfileResponse) => {
          if (this.userData === undefined) {
            this.hasMoreUserProfilePosts = !!data.pagination.next; // Check if there is more paginated data
            this.userData = data;
          } else {
            this.hasMoreUserProfilePosts = !!data.pagination.next; // Check if there is more paginated data
            // Append new results to existing posts
            this.userData.posts = [
              ...(this.userData.posts || []),
              ...data.posts,
            ];
          }
        },
        error: (error) => {
          this.userDataError = error;
        },
      });
  }

  // Function to load more paginated user profile posts for the Ionic infinite scroll component
  loadMoreProfilePosts(event: Event) {
    // Increment the current page of paginated user posts data
    this.currentUserProfilePostsPage++;

    // Call the service api with the updated page parameter
    this.fetchUser(this.userId);

    setTimeout(() => {
      // Complete the infinite scroll event to indicate that loading is done
      (event as InfiniteScrollCustomEvent).target.complete();
      // Scroll back to the previous position
    }, 500);
  }

  // Function to follow a user with a specified id
  followUser(userId: number) {
    // Call the service API function to follow the user
    this.followService
      .followUser(userId)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: (response) => {
          if (
            response &&
            response.follow_status &&
            this.userData !== undefined
          ) {
            // update the follow status property in the userData state
            this.userData.follow_status = response.follow_status;
          } else {
            console.error(
              'An error occurred while processing your request. Please try again later.'
            );
            // Display a toast message to alert the user an error occured
            this.followUserErrorToast();
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
          if (response && this.userData !== undefined) {
            // update the follow status property in the userData state
            this.userData.follow_status = response.follow_status;
          } else {
            console.error(
              'An error occurred while processing your request. Please try again later.'
            );
            // Display a toast message to alert the user an error occured
            this.unfollowUserErrorToast();
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

  // Changes the selected tab in the tablist
  selectTab(tabName: string): void {
    this.isSelectedTab = tabName;
  }

  ngOnDestroy(): void {
    // Complete the `destroyed$` Subject to signal unsubscription to any ongoing observables
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
