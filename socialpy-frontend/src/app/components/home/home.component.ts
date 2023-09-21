import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { InfiniteScrollCustomEvent } from '@ionic/angular';

import { Subscription, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { Store } from '@ngrx/store';
import { AppState } from 'src/app/store/app.state';
import {
  selectUserFeedData,
  selectUserFeedHasMoreData,
  selectUserFeedLoading,
  selectUserFeedError,
} from 'src/app/store/selectors/user-feed.selector';
import {
  selectLikedPostIds,
  selectPostActionError,
} from 'src/app/store/selectors/post-actions.selector';

import {
  likePost,
  unlikePost,
} from 'src/app/store/post-actions/post-actions.actions';
import * as UserFeedActions from 'src/app/store/user-feed/user-feed.actions';

import timeAgoFromString from 'src/utilities/dateTime';

import { faHeart, faComment } from '@fortawesome/free-regular-svg-icons';
import {
  faUser,
  faCircle,
  faHeart as faHeartSolid,
} from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent implements OnInit, OnDestroy {
  constructor(
    private router: Router,
    private store: Store<AppState> // NgRx store for managing application state, using our defined store configuration <AppState>
  ) {}

  private destroyed$: Subject<void> = new Subject<void>(); // Subject to track component destruction for subscription cleanup
  private subscriptions: Subscription[] = []; // Array to store active subscriptions to observables

  // Font Awesome icons
  faUser = faUser;
  faCircle = faCircle;
  faHeart = faHeart;
  faHeartSolid = faHeartSolid;
  faComment = faComment;

  initialLoadComplete = false; // Tracks the loading status for the initial loading of the page

  currentUserFeedPage = 1; // keep track of the current page of user feed content (for pagination)
  hasMoreUserFeedData: boolean = false; // Keeps track if there is more paginated data

  userFeedError: any = null; // Tracks if any errors occur while fetching feed posts
  userFeedPosts: any[] = []; // Contains the feed post data
  // Define a Set to keep track of IDs of unique post in the feed so repeated posts are not added when applying pagination
  private uniquePostIds = new Set<number>();

  postActionsError: any = null; // Tracks if any errors occur while liking/unliking a post
  likedPostIds: number[] = []; // Contains the IDs of posts that were liked by the user
  // Map to track how each feed post's like count should be changed (incremented/decremented) based on whether the user liked it or not
  feedPostLikeCounterChange: { [postId: number]: number } = {};

  isAlertOpen: boolean = false; // Tracks the status of the alert element
  // Alert button displays a log in button to return the user to the log in page
  alertButtons = [
    {
      text: 'Log In',
      handler: () => {
        this.goToLoginPage();
      },
    },
  ];

  ngOnInit(): void {
    // Dispatch the action to load user feed
    this.store.dispatch(
      UserFeedActions.loadUserFeed({ page: this.currentUserFeedPage })
    );

    // Subscribe to listen to any changes in the UserFeedState's loading property
    this.subscriptions.push(
      this.store
        .select(selectUserFeedLoading)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((loading) => {
          if (!loading) {
            this.initialLoadComplete = true;
          }
        })
    );

    // Subscribe to listen to any changes in the UserFeedState's error property
    this.subscriptions.push(
      this.store
        .select(selectUserFeedError)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((error) => {
          this.userFeedError = error;
        })
    );

    // Subscribe to listen to any changes in the UserFeedState's postData property (this keeps track of all the feed data the user will see)
    this.subscriptions.push(
      this.store
        .select(selectUserFeedData)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((postData) => {
          // Since each time the selectUserFeedData is changed, the entire postData state is returned with old and
          // new posts, we must filter out the old posts so we dont duplicate it in our userFeedPosts array
          const newPosts = postData.filter(
            (newPost) => !this.uniquePostIds.has(newPost.id)
          );

          // Update the Set with the IDs of the new posts
          newPosts.forEach((newPost) => {
            this.uniquePostIds.add(newPost.id);
          });

          // Append the new posts to the existing userFeedPosts array
          this.userFeedPosts = [
            ...this.userFeedPosts,
            ...newPosts.map((post) => ({
              ...post,
              formattedTimeAgo: timeAgoFromString(post.created_at),
            })),
          ];
        })
    );

    this.subscriptions.push(
      this.store
        .select(selectUserFeedHasMoreData)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((hasMoreData) => {
          this.hasMoreUserFeedData = hasMoreData;
        })
    );

    // Subscribe to listen to any changes in the LikedPostStates's likedIds property (this keeps track of all the posts the user liked)
    this.subscriptions.push(
      this.store
        .select(selectLikedPostIds)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((likedIds) => {
          this.likedPostIds = likedIds;
        })
    );

    // Subscribe to listen to any changes in the LikedPostStates's error property
    this.subscriptions.push(
      this.store
        .select(selectPostActionError)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((error) => {
          this.postActionsError = error;
        })
    );
  }

  loadMoreFeed(event: Event) {
    // Increment the current page of paginated user feed data
    this.currentUserFeedPage++;

    // Dispatch the action with the updated page parameter
    this.store.dispatch(
      UserFeedActions.loadUserFeed({ page: this.currentUserFeedPage })
    );

    setTimeout(() => {
      // Complete the infinite scroll event to indicate that loading is done
      (event as InfiniteScrollCustomEvent).target.complete();
      // Scroll back to the previous position
    }, 500);
  }

  setOpen(isOpen: boolean) {
    this.isAlertOpen = isOpen;
  }

  // Check if a post is liked by the user
  isPostLiked(postId: number): boolean {
    return this.likedPostIds.includes(postId);
  }

  // Toggle like/unlike for a post
  toggleLike(postId: number) {
    // Check if the post is already liked
    const isLiked = this.isPostLiked(postId);

    if (isLiked) {
      // Unlike the post
      this.store.dispatch(unlikePost({ postId }));

      // Update the like count in the map
      if (this.feedPostLikeCounterChange[postId]) {
        // If the post already exists in the map, decrease its like count change by 1
        // This accounts for unliking a previously liked post
        this.feedPostLikeCounterChange[postId] -= 1;
      } else {
        // If the post is not in the map, set its like count change to -1
        // This accounts for unliking a post just after page load
        this.feedPostLikeCounterChange[postId] = -1;
      }
    } else {
      // Like the post
      this.store.dispatch(likePost({ postId }));

      // Update the like count in the map
      if (this.feedPostLikeCounterChange[postId]) {
        // If the post exists in the map, increase its like count by 1
        // This accounts for liking a previously unliked post
        this.feedPostLikeCounterChange[postId] += 1;
      } else {
        // If the post is not in the map, set its like count to 1
        // This accounts for liking a post just after page load
        this.feedPostLikeCounterChange[postId] = 1;
      }
    }

    // Set isAlertOpen to true when an error occurs
    this.isAlertOpen = !!this.postActionsError;
  }

  // Redirect the user to the profile page associated with the user they are attempting to view
  goToUserProfilePage(userId: string) {
    this.router.navigate(['/profile', userId]);
  }

  goToLoginPage() {
    this.router.navigate(['/login']);
  }

  ngOnDestroy(): void {
    // Unsubscribe from all subscriptions in the `subscriptions` array
    this.subscriptions.forEach((subscription) => subscription.unsubscribe());

    // Complete the `destroyed$` Subject to signal unsubscription to any ongoing observables
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
