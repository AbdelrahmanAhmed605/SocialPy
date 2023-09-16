import { createAction, props } from '@ngrx/store';
import { Post } from './user-feed.model';

// Action to initiate fetching the user's feed
export const loadUserFeed = createAction('[User Feed] Load User Feed');

// Action to handle successful fetching of the user's feed
export const loadUserFeedSuccess = createAction(
  '[User Feed] Load User Feed Success',
  props<{ postData: Post[] }>() // Use the Post[] type for postData
);

// Action to handle failure when fetching the user's feed
export const loadUserFeedFailure = createAction(
  '[User Feed] Load User Feed Failure',
  props<{ error: any }>()
);
