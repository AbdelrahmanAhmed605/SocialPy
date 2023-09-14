import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Store } from '@ngrx/store';

import { Subscription, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AppState } from 'src/app/store/app.state';
import {
  selectUserFeedData,
  selectUserFeedLoading,
  selectUserFeedError,
} from 'src/app/store/selectors/user-feed.selector';
import { selectLikedPostIds } from 'src/app/store/selectors/post-actions.selector';

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
  // Font Awesome icons
  faUser = faUser;
  faCircle = faCircle;
  faHeart = faHeart;
  faHeartSolid = faHeartSolid;
  faComment = faComment;

  userFeedPosts: any[] = []; // Contains the feed post data
  likedPostIds: number[] = []; // Contains the IDs of posts that were liked by the user
  loading: boolean = false; // Tracks the loading status of feed posts being fetched
  error: any = null; // Tracks if any errors occur while fetching feed posts

  private destroyed$: Subject<void> = new Subject<void>();
  private subscriptions: Subscription[] = [];

  constructor(
    private router: Router,
    private store: Store<AppState> // Specify the AppState type
  ) {}

  ngOnInit(): void {
    // Dispatch the action to load user feed
    this.store.dispatch(UserFeedActions.loadUserFeed());

    // Subscribe to listen to any changes in the UserFeedState's loading property
    this.subscriptions.push(
      this.store
        .select(selectUserFeedLoading)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((loading) => {
          this.loading = loading;
        })
    );

    // Subscribe to listen to any changes in the UserFeedState's error property
    this.subscriptions.push(
      this.store
        .select(selectUserFeedError)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((error) => {
          this.error = error;
        })
    );

    // Subscribe to listen to any changes in the UserFeedState's postData property (this keeps track of all the feed data the user will see)
    this.subscriptions.push(
      this.store
        .select(selectUserFeedData)
        .pipe(takeUntil(this.destroyed$))
        .subscribe((postData) => {
          this.userFeedPosts = postData.map((post) => ({
            ...post,
            // Format the post data with a string which determines the time of when a post was created relative to the current time

            formattedTimeAgo: timeAgoFromString(post.created_at),
          }));
          console.log('Updated userFeedPosts:', this.userFeedPosts);
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
    } else {
      // Like the post
      this.store.dispatch(likePost({ postId }));
    }
  }

  // Redirect the user to the profile page associated with the user they are attempting to view
  goToUserProfilePage(userId: string) {
    this.router.navigate(['/profile', userId]);
  }

  ngOnDestroy(): void {
    // Unsubscribe from all subscriptions in the `subscriptions` array
    this.subscriptions.forEach((subscription) => subscription.unsubscribe());

    // Complete the `destroyed$` Subject to signal unsubscription to any ongoing observables
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
