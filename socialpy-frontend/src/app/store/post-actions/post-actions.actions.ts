import { createAction, props } from '@ngrx/store';

// Action to initiate liking a post with a specific postId
export const likePost = createAction(
  '[Post Actions] Like Post',
  props<{ postId: number }>() // Accepts a postId as a payload
);

// Action to indicate that the "like" operation on a post was successful.
export const likePostSuccess = createAction(
  '[Post Actions] Like Post Success',
  props<{ postId: number }>()
);

// Create an action to "unlike" a post with a specific postId.
export const unlikePost = createAction(
  '[Post Actions] Unlike Post',
  props<{ postId: number }>()
);

// Action to indicate that the "unlike" operation on a post was successful.
export const unlikePostSuccess = createAction(
  '[Post Actions] Unlike Post Success',
  props<{ postId: number }>()
);
