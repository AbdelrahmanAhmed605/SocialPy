import { createAction, props } from '@ngrx/store';

// Action to get the current theme of the application
export const getAppTheme = createAction('[App Theme] Get App Theme');

// Action to set the theme of the application
export const setAppTheme = createAction(
  '[App Theme] Set App Theme',
  props<{ isDarkTheme: boolean }>()
);

// Action to toggle the theme of the application
export const toggleAppTheme = createAction('[App Theme] Toggle App Theme');