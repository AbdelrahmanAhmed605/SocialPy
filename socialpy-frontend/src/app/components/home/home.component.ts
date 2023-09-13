import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { Store } from '@ngrx/store';
import { Subject } from 'rxjs';

import {
  likePost,
  unlikePost,
} from 'src/app/store/post-actions/post-actions.actions';
import * as UserFeedActions from 'src/app/store/user-feed/user-feed.actions';
import { AppState } from 'src/app/store/app.state';
import {
  selectUserFeedData,
  selectUserFeedLoading,
  selectUserFeedError,
} from 'src/app/store/selectors/user-feed.selector';
import { selectLikedPostIds } from 'src/app/store/selectors/post-actions.selector';

import { UserService } from 'src/app/api-services/user/user.service';
import { AuthService } from 'src/utilities/auth';
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
export class HomeComponent implements OnInit {
  faUser = faUser;
  faCircle = faCircle;
  faHeart = faHeart;
  faHeartSolid = faHeartSolid;
  faComment = faComment;

  userFeedPosts: any[] = [];
  likedPostIds: number[] = [];
  loading: boolean = false;
  error: any = null;

  constructor(
    private router: Router,
    private store: Store<AppState> // Specify the AppState type
  ) {}

  ngOnInit(): void {
    // Dispatch the action to load user feed
    this.store.dispatch(UserFeedActions.loadUserFeed());

    this.store.select(selectUserFeedLoading).subscribe((loading) => {
      this.loading = loading;
    });

    this.store.select(selectUserFeedError).subscribe((error) => {
      this.error = error;
    });

    // Select the postData and likedPostIds
    this.store.select(selectUserFeedData).subscribe((postData) => {
      this.userFeedPosts = postData.map((post) => ({
        ...post,
        formattedTimeAgo: timeAgoFromString(post.created_at),
      }));
    });

    this.store.select(selectLikedPostIds).subscribe((likedIds) => {
      this.likedPostIds = likedIds;
    });
  }

  isPostLiked(postId: number): boolean {
    return this.likedPostIds.includes(postId);
  }

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
}
