import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { Store } from '@ngrx/store';
import { AppState } from 'src/app/store/app.state';
import { selectAppTheme } from 'src/app/store/selectors/app-theme.selector';
import { toggleAppTheme } from 'src/app/store/app-theme/app-theme.actions';

import { takeUntil } from 'rxjs/operators';
import { Subject } from 'rxjs';

import { UserService } from 'src/app/api-services/user/user.service';
import { AuthService } from 'src/utilities/auth';

@Component({
  selector: 'app-user-login',
  templateUrl: './user-login.component.html',
  styleUrls: ['./user-login.component.css'],
})
export class UserLoginComponent implements OnInit, OnDestroy {
  // Injects FormBuilder, Router, and UserService dependencies
  constructor(
    private fb: FormBuilder,
    private router: Router, // Router for navigating between pages
    private userService: UserService, // UserService for user-related API operations
    private authService: AuthService, // AuthService for authentication related operations
    private store: Store<AppState> // NgRx store for managing application state, using our defined store configuration <AppState>
  ) {}

  private destroyed$: Subject<void> = new Subject<void>(); // Subject to track component destruction for subscription cleanup

  isDarkTheme!: boolean; // Represents the current selection of the app's theme

  // Initialize form groups and error variables
  loginForm: FormGroup = new FormGroup({});
  formSubmitted = false;

  loginError = '';
  generalError = '';
  loginFieldEdited = false;

  // Define validation error messages for form fields
  validationMessages = {
    username: {
      required: 'Username is required.',
      maxLength: 'Username cannot exceed 255 characters.',
    },
    password: {
      required: 'Password is required.',
    },
  };

  ngOnInit() {
    // Call the form creation function during component initialization
    this.createForm();

    // Subscribe to changes in the app theme state and update the component's
    // 'isDarkTheme' property accordingly. Use 'takeUntil' to automatically
    // unsubscribe when the component is destroyed to prevent memory leaks.
    this.store
      .select(selectAppTheme)
      .pipe(takeUntil(this.destroyed$))
      .subscribe((isDarkTheme) => {
        this.isDarkTheme = isDarkTheme;
      });
  }

  // Dispatch the toggleAppTheme action
  // The reducer will change the isDarkTheme property in the App store's `selectAppTheme` selector
  // The effect middleware of the action will set the toggled theme to the document body
  toggleAppTheme() {
    this.store.dispatch(toggleAppTheme());
  }

  // Create the form structure and validation rules
  createForm() {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.maxLength(255)]],
      password: ['', Validators.required],
    });
  }

  // Clear error messages for form fields
  clearFieldErrors() {
    this.loginError = '';
    this.loginFieldEdited = false;
  }

  // Handle the login form submission
  login() {
    this.formSubmitted = true;
    this.clearFieldErrors();

    if (this.loginForm.valid) {
      const formData = {
        username: this.loginForm.value.username.toLowerCase(),
        password: this.loginForm.value.password,
      };

      // Send a request to the login API
      this.userService.loginUser(formData).subscribe(
        (response: any) => {
          // Place the user's authentication token in the local storage
          this.authService.login(response.token);
          // Redirect user to the homepage
          this.router.navigate(['/']);
        },
        (error: any) => {
          // Handle errors
          console.error('Error loggin in:', error);
          if (error.error) {
            this.loginError = error.error.error;
          } else {
            this.generalError = 'An error occurred. Please try again later.';
          }
        }
      );
    } else {
      console.error('Form is incomplete. Please fill in all fields.');
    }
  }

  // Redirect the user to the signup page if they don't have an account
  goToSignupPage() {
    this.router.navigate(['/signup']);
  }

  // Unsubscribe from all subscriptions when the component is destroyed
  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
