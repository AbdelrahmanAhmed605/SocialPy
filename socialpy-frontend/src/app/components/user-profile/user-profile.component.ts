import { Component, OnInit, HostListener, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ToastController, Platform } from '@ionic/angular';

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
  userData!: UserProfileResponse; // Contains the user's profile data
  userDataError: any = null; // Tracks if any errors occur while fetching user profile data

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

  // Call the service api function to retrieve the list of users who liked a post
  async fetchUser(userId: number) {
    this.userService
      .getUserProfile(userId)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: (data: UserProfileResponse) => {
          this.userData = data;
        },
        error: (error) => {
          this.userDataError = error;
        },
      });
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
          if (response) {
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
