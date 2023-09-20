import { Injectable, Renderer2, RendererFactory2 } from '@angular/core';

import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';

import { tap, withLatestFrom, switchMap } from 'rxjs/operators';

import { toggleAppTheme, getAppTheme, setAppTheme } from './app-theme.actions';
import { selectAppTheme } from '../selectors/app-theme.selector';
import { AppState } from '../app.state';

@Injectable()
export class AppThemeEffects {
  private renderer: Renderer2;
  constructor(
    private actions$: Actions, // Inject the NgRx Actions service
    private store: Store<AppState>, // Inject the NgRx Store service with our defined application's state
    private rendererFactory: RendererFactory2
  ) {
    // Create a renderer instance using the RendererFactory2 to allow DOM manipulation
    this.renderer = this.rendererFactory.createRenderer(null, null);
  }

  // Effect to initialize the theme from localStorage when the app starts
  getAppTheme$ = createEffect(() =>
    this.actions$.pipe(
      ofType(getAppTheme),
      switchMap(() => {
        const storedTheme = localStorage.getItem('app-theme');
        const appTheme = storedTheme || 'light'; // Use the stored theme or default to light if there is no existing theme

        // Apply the theme to document.body
        this.renderer.setAttribute(
          document.body,
          'color-theme',
          appTheme === 'dark' ? 'dark' : 'light'
        );

        // Dispatch action to set the app theme in the store
        return [setAppTheme({ isDarkTheme: appTheme === 'dark' })];
      })
    )
  );

  // Effect to handle toggling of the application's theme
  toggleAppTheme$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(toggleAppTheme),
        withLatestFrom(this.store.select(selectAppTheme)),
        // isDarkTheme is retrieved from the 'selectAppTheme' selector in the App's Store
        // The isDarkTheme contains the new theme of the application that was toggled using the reducer
        tap(([action, isDarkTheme]) => {
          // Update localStorage with the new theme
          localStorage.setItem('app-theme', isDarkTheme ? 'dark' : 'light');

          // Update the 'color-theme' attribute on the <body> element
          this.renderer.setAttribute(
            document.body,
            'color-theme',
            isDarkTheme ? 'dark' : 'light'
          );
        })
      ),
    { dispatch: false } // This effect doesn't dispatch any new actions
  );
}
