import { createReducer, on } from '@ngrx/store';
import { likePostSuccess, unlikePost } from './post-actions.actions';

// Define the shape of the LikedPostsState
export interface LikedPostsState {
  likedPostIds: number[]; // Stores the id of posts that were liked by the user
}

// Define the initial state for the UserFeedState
const initialState: LikedPostsState = {
  likedPostIds: [],
};

export const postActionsReducer = createReducer(
  initialState,
  // Listen to the 'likePostSuccess' action and update the state accordingly.
  on(likePostSuccess, (state, { postId }) => ({
    ...state,
    likedPostIds: [...state.likedPostIds, postId], // Add the new postId to the likedPostIds state property
  })),

  // Listen to the 'unlikePost' action and update the state accordingly.
  on(unlikePost, (state, { postId }) => ({
    ...state,
    likedPostIds: state.likedPostIds.filter((id) => id !== postId), // Remove the postId from the likedPostIds state property
  }))
);
