import { createSelector, createFeatureSelector } from '@ngrx/store';
import { UserFeedState } from '../user-feed/user-feed.reducer';

/* 
Create a feature selector to select the userFeed feature state. Feature selectors access the state of a specific 
feature module within the store. In this case, it selects the 'userFeed' feature state from the store.
*/
const selectUserFeedFeature = createFeatureSelector<UserFeedState>('userFeed');

// Selectors are used to make a central mechanism to allow different components and effect middlewares to 
// efficiently access and change data from the store's state.

// Create a selector function to select the entire UserFeedState
export const selectUserFeedState = createSelector(
  selectUserFeedFeature,
  (state: UserFeedState) => state
);

// Selector for the 'postData' property from the 'userFeed' feature state to allow efficient access to user feed data.
export const selectUserFeedData = createSelector(
  selectUserFeedState, // Use the selectUserFeedState selector
  (state: UserFeedState) => state.postData
);

// Selector for the 'hasMoreData' to allow components to detect if there is more paginated data
export const selectUserFeedHasMoreData = createSelector(
  selectUserFeedState, // Use the selectUserFeedState selector
  (state: UserFeedState) => state.hasMoreData
);

// Selector for 'loading' property to indicate if data is currently being fetched.
export const selectUserFeedLoading = createSelector(
  selectUserFeedState, // Use the selectUserFeedState selector
  (state: UserFeedState) => state.loading
);

/* 
Selector for 'error' property to indicate if any errors occur during data retrieval.
*/
export const selectUserFeedError = createSelector(
  selectUserFeedState, // Use the selectUserFeedState selector
  (state: UserFeedState) => state.error
);
