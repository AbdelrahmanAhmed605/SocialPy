import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { UserService } from '../api-services/user/user/user.service';
import AuthService from '../../utilities/auth';

@Component({
  selector: 'app-user-login',
  templateUrl: './user-login.component.html',
  styleUrls: ['./user-login.component.css'],
})
export class UserLoginComponent implements OnInit {
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

  // Injects FormBuilder, Router, and UserService dependencies
  constructor(
    private fb: FormBuilder,
    private router: Router, // Router for navigating between pages
    private userService: UserService // UserService for user-related API operations
  ) {}

  ngOnInit() {
    // Call the form creation function during component initialization
    this.createForm();
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
          AuthService.login(response.token);
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
}
