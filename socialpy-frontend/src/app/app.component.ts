import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { AppState } from './store/app.state';
import { getAppTheme } from './store/app-theme/app-theme.actions';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
})
export class AppComponent implements OnInit {
  constructor(private store: Store<AppState>) {}

  ngOnInit() {
    // Dispatch the getAppTheme action when the app starts.
    // The effect middleware of the action will set the theme to the document body
    this.store.dispatch(getAppTheme());
  }
}
