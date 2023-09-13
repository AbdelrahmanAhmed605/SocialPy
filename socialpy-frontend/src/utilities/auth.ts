import { Injectable } from '@angular/core';
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

  // Utility function to handle authentication token. This is to be used in API services that require authentication
  handleAuthenticationToken(): Observable<string> {
    const token = this.getToken();

    if (!token) {
      return throwError(
        () => new Error(this.authenticationTokenMissingErrorMessage)
      );
    }

    return of(token); // Return the token as an observable
  }

  // Helper function to check if an error is due to authentication error
  isAuthenticationError(error: any): boolean {
    return error.message === this.authenticationTokenMissingErrorMessage;
  }

  // Perform logout by removing the token from localStorage and redirecting to the main page
  logout(): void {
    localStorage.removeItem('id_token');
    window.location.assign('/');
  }
}
