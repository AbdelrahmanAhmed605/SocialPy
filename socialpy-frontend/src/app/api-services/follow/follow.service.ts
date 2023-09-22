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
    const followUserEndpoint = `follow/user/${userId}/`;

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // Like the specified post
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
    const unfollowUserEndpoint = `unfollow/user/${userId}/`;

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // Like the specified post
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
}
