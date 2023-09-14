import { createSelector, createFeatureSelector } from '@ngrx/store';
import { LikedPostsState } from '../post-actions/post-actions.reducer';

/* 
Create a feature selector to select the likedPosts feature state. Feature selectors are used to access the state 
of a specific feature module within the store. In this case, it selects the 'likedPosts' feature state from the store.
*/
const selectLikedPostsFeature =
  createFeatureSelector<LikedPostsState>('likedPosts');

/* 
Create a selector function to select the 'likedPostIds' property from the 'likedPosts' feature state. 
Selectors are used to make a central mechanism to allow different components and effect middlewares to efficiently 
access and change data from the store's state
*/
export const selectLikedPostIds = createSelector(
  selectLikedPostsFeature,  // Use the feature selector to access the 'likedPosts' feature state
  (state: LikedPostsState) => state.likedPostIds  // Select the 'likedPostIds' property from the state
);
