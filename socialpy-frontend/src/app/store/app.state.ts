import { ActionReducerMap } from '@ngrx/store';
import {
  LikedPostsState,
  postActionsReducer,
} from './post-actions/post-actions.reducer';
import { UserFeedState, userFeedReducer } from './user-feed/user-feed.reducer';
import { AppThemeState, appThemeReducer } from './app-theme/app-theme.reducer';

// The AppState interface defines the overall structure of the application's store state.
// It serves as a central location to describe the structure of different feature module states.
// Each property within AppState corresponds to a specific feature module's state.
export interface AppState {
  likedPosts: LikedPostsState;
  userFeed: UserFeedState;
  appTheme: AppThemeState;
}

// The 'reducers' variable specifies how the reducers from different feature modules are combined
// into a single reducer for the entire application. This centralizes the state management and
// serves as a mechanism to define the application's overall state structure by associating
// each feature module's reducer with its corresponding state.
export const reducers: ActionReducerMap<AppState> = {
  likedPosts: postActionsReducer, // Reducer for the 'likedPosts' feature module
  userFeed: userFeedReducer, // Reducer for the 'userFeed' feature module
  appTheme: appThemeReducer, // Reducer for the 'appTheme' feature module
};
