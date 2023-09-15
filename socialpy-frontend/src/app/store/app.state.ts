import { ActionReducerMap } from '@ngrx/store';
import {
  LikedPostsState,
  postActionsReducer,
} from './post-actions/post-actions.reducer';
import { UserFeedState, userFeedReducer } from './user-feed/user-feed.reducer'; // Import UserFeedState and userFeedReducer

// The AppState interface defines the overall structure of the application's store state.
// It serves as a central location to describe the structure of different feature module states.
// Each property within AppState corresponds to a specific feature module's state (ex: 'likedPosts','userFeed').
export interface AppState {
  likedPosts: LikedPostsState;
  userFeed: UserFeedState;
}

// The 'reducers' variable specifies how the reducers from different feature modules are combined.
// These reducers are placed together into a single reducer for the entire application.
// This centralizes the state management and serves as a mechanism to define the application's overall structure.
export const reducers: ActionReducerMap<AppState> = {
  likedPosts: postActionsReducer, // Reducer for the 'likedPosts' feature module
  userFeed: userFeedReducer,     // Reducer for the 'userFeed' feature module
};
