import { createSelector, createFeatureSelector } from '@ngrx/store';
import { AppThemeState } from '../app-theme/app-theme.reducer';

/* 
Create a feature selector to select the AppThemeState feature state. Feature selectors are used to access the state 
of a specific feature module within the store. In this case, it selects the 'appTheme' feature state from the store.
*/
const selectAppThemeFeature =
  createFeatureSelector<AppThemeState>('appTheme');

/* 
Create a selector function to select the 'isDarkTheme' property from the 'appTheme' feature state. 
Selectors are used to make a central mechanism to allow different components and effect middlewares to efficiently 
access and change data from the store's state
*/
export const selectAppTheme = createSelector(
  selectAppThemeFeature, // Use the feature selector to access the 'appTheme' feature state
  (state: AppThemeState) => state.isDarkTheme // Select the 'isDarkTheme' property from the state
);
