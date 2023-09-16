import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';


@Injectable({
  providedIn: 'root', // This makes the service a singleton across the application.
})
export class AuthService {
  private authenticationTokenMissingErrorMessage =
    'Authentication token is missing.';

  // Get the token from localStorage
  getToken(): string | null {
    return localStorage.getItem('id_token');
  }

  // Perform login by storing the token in localStorage
  login(idToken: string): void {
    localStorage.setItem('id_token', idToken);
  }

  // Check if the user is logged in
  loggedIn(): boolean {
    const token = this.getToken();
    return !!token;
  }

  // Utility function to handle authentication token.
  // This is to be used in API services that require authentication (we define it as Observable since Angular HTTPClient handles Observables )
  handleAuthenticationToken(): Observable<string> {
    const token = this.getToken();

    if (!token) {
      // Create a custom HttpErrorResponse with status code 401
      const errorResponse = new HttpErrorResponse({
        error: this.authenticationTokenMissingErrorMessage,
        status: 401, // 401 represents Unauthorized status
        statusText: 'Unauthorized', // Status text for 401 error
      });

      return throwError(() => errorResponse);
    }

    return of(token); // Return the token as an observable
  }

  // Helper function to check if an error is due to authentication error
  isAuthenticationError(error: any): boolean {
    return (
      error.error === this.authenticationTokenMissingErrorMessage ||
      error.status == 401
    );
  }

  // Perform logout by removing the token from localStorage and redirecting to the main page
  logout(): void {
    localStorage.removeItem('id_token');
    window.location.assign('/');
  }
}
