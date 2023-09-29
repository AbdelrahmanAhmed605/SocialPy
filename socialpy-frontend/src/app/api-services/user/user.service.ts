import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { Observable, throwError } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';

import { API_BASE_URL } from '../api.config';
import { AuthService } from 'src/utilities/auth';

@Injectable({
  providedIn: 'root',
})
export class UserService {
  constructor(private http: HttpClient, private authService: AuthService) {}

  // API call to create a new user
  createUser(userData: any): Observable<any> {
    const createUserEndpoint = 'users';
    // Make the POST request with userData
    return this.http.post(`${API_BASE_URL}/${createUserEndpoint}/`, userData, {
      withCredentials: true,
    });
  }

  // API call to allow user to login
  loginUser(userData: any): Observable<any> {
    const loginEndpoint = 'login';
    // Make a POST request to the login route
    return this.http.post(`${API_BASE_URL}/${loginEndpoint}/`, userData, {
      withCredentials: true,
    });
  }

  /* 
- authService.handleAuthenticationToken is a utility function that returns the user token if found
 or an error that will be thrown into the service's catchError if not found
 - .pipe is used to chain multiple operators together in a sequence (ex: switchMap and catchError)
 - Use switchMap to transition from the handleAuthenticationToken's returned Observable string to the HTTP
request's returned Observable structure. SwitchMap also preserves the token value returned from handleAuthenticationToken
*/

  // Get the user's feed data while handling authentication
  getUserFeed(page: number): Observable<any> {
    const feedEndpoint = `feed/?page=${page}`;

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token returned from handleAuthenticationToken
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        return this.http.get(`${API_BASE_URL}/${feedEndpoint}`, {
          headers,
          withCredentials: true,
        });
      }),
      catchError((error) => {
        // throw the error
        return throwError(() => error);
      })
    );
  }

  // Get a users profile (user information and posts)
  getUserProfile(userId: number): Observable<any> {
    const userProfileEndpoint = `user/profile/${userId}`;

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token returned from handleAuthenticationToken
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        return this.http.get(`${API_BASE_URL}/${userProfileEndpoint}`, {
          headers,
          withCredentials: true,
        });
      }),
      catchError((error) => {
        // throw the error
        return throwError(() => error);
      })
    );
  }
}
