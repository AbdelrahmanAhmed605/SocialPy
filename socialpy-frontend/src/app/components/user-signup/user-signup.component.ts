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
  selector: 'app-user-signup',
  templateUrl: './user-signup.component.html',
  styleUrls: ['./user-signup.component.css'],
})
export class UserSignupComponent implements OnInit, OnDestroy {
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
  signupForm: FormGroup = new FormGroup({});
  formSubmitted = false;

  emailError = '';
  emailFieldEdited = false;

  usernameError = '';
  usernameFieldEdited = false;

  generalError = '';

  // Define validation error messages for form fields
  validationMessages = {
    email: {
      required: 'Email is required.',
      pattern: 'Please enter a valid email address.',
      maxLength: 'Email must not exceed 255 characters.',
    },
    username: {
      required: 'Username is required.',
      maxLength: 'Username must not exceed 255 characters.',
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
    this.signupForm = this.fb.group({
      email: [
        '',
        [
          Validators.required,
          Validators.pattern(
            '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,4}$'
          ),
          Validators.maxLength(255),
        ],
      ],
      username: ['', [Validators.required, Validators.maxLength(255)]],
      password: ['', Validators.required],
    });
  }

  // Clear error messages for form fields
  clearFieldErrors() {
    this.emailError = '';
    this.emailFieldEdited = false;
    this.usernameError = '';
    this.usernameFieldEdited = false;
    this.generalError = '';
  }

  // Handle the signup form submission
  signup() {
    this.formSubmitted = true;
    this.clearFieldErrors();

    if (this.signupForm.valid) {
      const formData = {
        email: this.signupForm.value.email.toLowerCase(),
        username: this.signupForm.value.username.toLowerCase(),
        password: this.signupForm.value.password,
      };

      // Send a request to create a new user
      this.userService.createUser(formData).subscribe(
        (response: any) => {
          // Place the new user's authentication token in the local storage
          this.authService.login(response.token);
          this.router.navigate(['/']);
        },
        (error: any) => {
          console.error('Error creating user:', error);

          // Handle specific error cases for username and email fields
          if (error.error.username) {
            this.usernameError = error.error.username.join(', ');
          }
          if (error.error.email) {
            this.emailError = error.error.email.join(', ');
          }
          if (!error.error.username && !error.error.email) {
            this.generalError = 'An error occurred. Please try again later.';
          }
        }
      );
    } else {
      console.error('Form is incomplete. Please fill in all fields.');
    }
  }

  // Redirect the user to the login page if they already have an account
  goToLoginPage() {
    this.router.navigate(['/login']);
  }

  // Unsubscribe from all subscriptions when the component is destroyed
  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
