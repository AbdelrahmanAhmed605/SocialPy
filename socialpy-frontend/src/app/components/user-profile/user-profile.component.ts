import { Component, OnInit, HostListener, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import {
  ToastController,
  ModalController,
  Platform,
  InfiniteScrollCustomEvent,
} from '@ionic/angular';

import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { UserService } from 'src/app/api-services/user/user.service';
import { FollowService } from 'src/app/api-services/follow/follow.service';

import { UserProfileResponse } from 'src/app/interface-types/user-profile.model';

import { UserConnectionsModalComponent } from '../user-connections-modal/user-connections-modal.component';
import { SinglePostModalComponent } from '../single-post-modal/single-post-modal.component';

import {
  faUser,
  faTableCells,
  faHeart,
  faComment,
  faLock,
  faCamera,
} from '@fortawesome/free-solid-svg-icons';

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
    private platform: Platform, // service for detecting screen width
    private modalCtrl: ModalController
  ) {
    // Determine if the screen is considered large or small based on the initial platform width.
    this.isLargeScreen = this.platform.width() > 736;
  }

  // Font Awesome icons
  faUser = faUser;
  faTableCells = faTableCells;
  faHeart = faHeart;
  faComment = faComment;
  faLock = faLock;
  faCamera = faCamera;

  isLargeScreen!: boolean; // determines if the width of the device is large or small

  selectedTab: string = 'posts'; // checks which tab in the tablist is currently selected. The default is "posts"

  userId!: number; // Contains the id of the user being viewed in the component
  userData: UserProfileResponse | undefined; // Contains the user's profile data

  userDataError: any = null; // Tracks if any errors occur while fetching user profile data

  currentUserProfilePostsPage = 1; // keep track of the current page of user's profile posts (for pagination)
  hasMoreUserProfilePosts: boolean = false; // Keeps track if there is more paginated profile posts

  private destroyed$ = new Subject<void>(); // Subject to track component destruction for subscription cleanup

  ngOnInit() {
    // Clean up the subscriptions and rest the destoryed$ subject
    // This ensures a clean state when navigating to this same component but with a different user in the route parameter
    this.cleanSubscriptions();

    // Get the userId from the route parameter and fetch their data
    this.activatedRoute.paramMap
      .pipe(takeUntil(this.destroyed$))
      .subscribe((params) => {
        const userIdParam = params.get('userId'); // get the userId from the route
        if (userIdParam !== null) {
          this.resetComponentState(); // Re-initialize the component's state
          this.userId = parseInt(userIdParam, 10);
          this.fetchUser(this.userId); // fetch the user's data
        } else {
          // Handle the case when 'userId' is null (not present in the params).
          this.userDataError = {
            message: 'User ID not found in route parameters',
            status: 404,
          };
        }
      });
  }

  // Clean up and reset the destroyed$ subject to manage subscriptions
  cleanSubscriptions() {
    // Unsubscribe from any ongoing subscriptions
    if (this.destroyed$) {
      this.destroyed$.next();
      this.destroyed$.complete();
    }
    // Recreate the destroyed$ subject
    this.destroyed$ = new Subject<void>();
  }

  // Function to reset the component's state variables to their initial values
  private resetComponentState() {
    this.userId = -1;
    this.userData = undefined;
    this.userDataError = null;
    this.currentUserProfilePostsPage = 1;
    this.hasMoreUserProfilePosts = false;
    this.selectedTab = 'posts';
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
          // UserData is undefined the first time we populate the userData so we set userData = data
          if (this.userData === undefined) {
            this.userData = data;
            this.hasMoreUserProfilePosts = !!data.pagination.next; // Check if there is more paginated data
          } else {
            // For subsequent calls (for loading more profile posts) where userData is already defined,
            // we append the posts to the existing posts array
            this.userData.posts = [
              ...(this.userData.posts || []),
              ...data.posts,
            ];
            this.hasMoreUserProfilePosts = !!data.pagination.next; // Check if there is more paginated data
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
            // If the follow status is accepted (not pending request to private user) then increment the profiles
            // follower count
            if (response.follow_status === 'accepted') {
              this.userData.num_followers += 1;
            }
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
            // Check what the follow status was before unfollowing. If they were accepted (not pending) then
            // decrement the follower count
            if (this.userData.follow_status == 'accepted') {
              this.userData.num_followers -= 1;
            }
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
    this.selectedTab = tabName;
  }

  // Function to create the modal to display the list of followers or followings for a specified user
  async openUserConnectionsModal(userId: number, connectionType: string) {
    const modalOptions: any = {
      component: UserConnectionsModalComponent,
      componentProps: {
        userId: userId, // Pass the userId to the modal component
        connectionType: connectionType, // string indicating whether the list is "followers" or "following"
      },
    };

    // Check if the device is small (width less than 768 px)
    // If the device is small then apply breakpoints to create an ionic sheet modal view for the modal
    if (this.platform.width() < 768) {
      modalOptions.breakpoints = [0, 0.7, 1.0];
      modalOptions.initialBreakpoint = 1.0;
    }

    // Create the modal and present it
    const modal = await this.modalCtrl.create(modalOptions);
    modal.present();
  }

  // Function to create the modal to display the view for the specified post
  async openSinglePostModal(postId: number) {
    const modal = await this.modalCtrl.create({
      component: SinglePostModalComponent,
      componentProps: {
        postId: postId, // Pass the postId to the modal component
      },
    });

    modal.present();
  }

  ngOnDestroy(): void {
    // Complete the `destroyed$` Subject to signal unsubscription to any ongoing observables
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
