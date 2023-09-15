import { createReducer, on } from '@ngrx/store';
import * as UserFeedActions from './user-feed.actions';
import { Post } from './user-feed.model';

// Define the shape of the UserFeedState
export interface UserFeedState {
  loading: boolean; // Indicates if the feed data is currently being loaded
  error: any; // Holds any error that occurred during the feed data loading
  postData: Post[]; // Stores the loaded user feed data
}

// Define the initial state for the UserFeedState
export const initialState: UserFeedState = {
  loading: false, // Initially, feed data is not being loaded
  error: null, // Initially, there are no errors
  postData: [], // Initially, the feed data is an empty array
};

// Create reducers to handle actions and perform changes to the UserFeedState
export const userFeedReducer = createReducer(
  initialState,

  // Action handler for 'loadUserFeed' action
  on(UserFeedActions.loadUserFeed, (state) => ({
    ...state,
    loading: true, // Set loading to true when 'loadUserFeed' is dispatched
    error: null, // Clear any previous errors
  })),

  // Action handler for 'loadUserFeedSuccess' action
  on(UserFeedActions.loadUserFeedSuccess, (state, { postData }) => ({
    ...state,
    loading: false, // Set loading to false when data is successfully loaded
    postData: [
      // Update the postData with unique posts from the loaded data
      ...state.postData,
      ...postData.filter(
        (newPost) =>
          !state.postData.some((existingPost) => existingPost.id === newPost.id)
      ),
    ],
  })),

  // Action handler for 'loadUserFeedFailure' action
  on(UserFeedActions.loadUserFeedFailure, (state, { error }) => ({
    ...state,
    loading: false, // Set loading to false when data loading fails
    error, // Store the error that occurred during loading
  }))
);
