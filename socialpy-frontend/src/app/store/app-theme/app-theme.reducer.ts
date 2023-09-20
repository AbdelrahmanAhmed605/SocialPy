import { createReducer, on } from '@ngrx/store';
import { toggleAppTheme, setAppTheme } from './app-theme.actions';

// Define the shape of the AppThemeState
export interface AppThemeState {
  isDarkTheme: boolean;
}

// Define initial state for the AppThemeState
const initialState: AppThemeState = {
  isDarkTheme: false,
};

export const appThemeReducer = createReducer(
  initialState,
  // sets the theme of the application to the prop that is passed
  on(setAppTheme, (state, { isDarkTheme }) => ({
    ...state,
    isDarkTheme,
  })),
  // toggles the theme of the application between light and dark
  on(toggleAppTheme, (state) => ({
    ...state,
    isDarkTheme: !state.isDarkTheme,
  }))
);
