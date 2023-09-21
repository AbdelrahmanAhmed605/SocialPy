import { createAction, props } from '@ngrx/store';
import { Post } from '../../interface-types/user-feed.model'; // Represents the structure of a post object received from the API.

// Action to initiate fetching the user's feed
export const loadUserFeed = createAction(
  '[User Feed] Load User Feed',
  props<{ page: number }>() // page prop refers to page of the paginated api data
);

// Action to handle successful fetching of the user's feed
export const loadUserFeedSuccess = createAction(
  '[User Feed] Load User Feed Success',
  props<{ postData: Post[]; hasMoreData: boolean }>() // hasMoreData checks api call to see if there is more paginated data
);

// Action to handle failure when fetching the user's feed
export const loadUserFeedFailure = createAction(
  '[User Feed] Load User Feed Failure',
  props<{ error: any }>()
);
