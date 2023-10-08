import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { Observable, throwError } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';

import { API_BASE_URL } from '../api.config';
import { AuthService } from 'src/utilities/auth';

@Injectable({
  providedIn: 'root',
})
export class FollowService {
  constructor(private http: HttpClient, private authService: AuthService) {}

  // API call to follow a user
  followUser(userId: number): Observable<any> {
    const followUserEndpoint = `follow/user/${userId}/`; // create the api endpoint

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // call the api endpoint to follow the user
        return this.http.post(`${API_BASE_URL}/${followUserEndpoint}`, null, {
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

  // API call to unfollow a user
  unfollowUser(userId: number): Observable<any> {
    const unfollowUserEndpoint = `unfollow/user/${userId}/`; // create the api endpoint

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // call the api endpoint to unfollow the user
        return this.http.post(`${API_BASE_URL}/${unfollowUserEndpoint}`, null, {
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

  // Get a paginated list (using page parameter) of users that follow the specified user (userId)
  // apply an optional username parameter to filter the results if provided
  getUsersFollowers(
    userId: number,
    page: number,
    username?: string
  ): Observable<any> {
    let userFollowersEndpoint = `follower_list/${userId}/?page=${page}`; // create the api endpoint

    // Append the username query parameter to the api endpoint if provided
    if (username) {
      userFollowersEndpoint += `&username=${encodeURIComponent(username)}`;
    }

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // call the api endpoint to get userId's followers
        return this.http.get(`${API_BASE_URL}/${userFollowersEndpoint}`, {
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

  // Get a paginated list (using page parameter) of users that the specified user (userId) is following
  // apply an optional username parameter to filter the results if provided
  getUsersFollowing(
    userId: number,
    page: number,
    username?: string
  ): Observable<any> {
    let userFollowingEndpoint = `following_list/${userId}/?page=${page}`; // create the api endpoint

    // Append the username query parameter to the api endpoint if provided
    if (username) {
      userFollowingEndpoint += `&username=${encodeURIComponent(username)}`;
    }

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // call the api endpoint to get userId's following
        return this.http.get(`${API_BASE_URL}/${userFollowingEndpoint}`, {
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
