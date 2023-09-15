import { createReducer, on } from '@ngrx/store';
import {
  likePost,
  likePostSuccess,
  likePostFailure,
  unlikePost,
  unlikePostSuccess,
  unlikePostFailure,
} from './post-actions.actions';

// Define the shape of the LikedPostsState
export interface LikedPostsState {
  likedPostIds: number[]; // Stores the id of posts that were liked by the user
  error: any; // Holds any error that occurred during the liking or unliking of a post
}

// Define the initial state for the UserFeedState
const initialState: LikedPostsState = {
  likedPostIds: [],
  error: null,
};

export const postActionsReducer = createReducer(
  initialState,

  // Action handler for 'likePost' action
  on(likePost, (state, { postId }) => ({
    ...state,
    error: null, // Clear any previous errors
  })),

  // Action handler for 'unlikePost' action
  on(unlikePost, (state, { postId }) => ({
    ...state,
    error: null, // Clear any previous errors
  })),

  // Listen to the 'likePostSuccess' action and update the state accordingly.
  on(likePostSuccess, (state, { postId }) => ({
    ...state,
    likedPostIds: [...state.likedPostIds, postId], // Add the new postId to the likedPostIds state property
    error: null,
  })),

  // Listen to the 'unlikePostSuccess' action and update the state accordingly.
  on(unlikePostSuccess, (state, { postId }) => ({
    ...state,
    likedPostIds: state.likedPostIds.filter((id) => id !== postId), // Remove the postId from the likedPostIds state property
    error: null,
  })),

  // Action handler for 'likePostFailure' action
  on(likePostFailure, (state, { error }) => ({
    ...state,
    error,
  })),

  // Action handler for 'unlikePostFailure' action
  on(unlikePostFailure, (state, { error }) => ({
    ...state,
    error,
  }))
);
