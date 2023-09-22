import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { Observable, throwError } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';

import { API_BASE_URL } from '../api.config';
import { AuthService } from 'src/utilities/auth';

@Injectable({
  providedIn: 'root',
})
export class PostService {
  constructor(private http: HttpClient, private authService: AuthService) {}

  /* 
- authService.handleAuthenticationToken is a utility function that returns the user token if found
 or an error that will be thrown into the service's catchError if not found
 - .pipe is used to chain multiple operators together in a sequence (ex: switchMap and catchError)
 - Use switchMap to transition from the handleAuthenticationToken's returned Observable string to the HTTP
request's returned Observable structure. SwitchMap also preserves the token value returned from handleAuthenticationToken
*/

  // Like a post by sending a POST request with authentication
  likePost(postId: number): Observable<any> {
    const likePostEndpoint = `post/${postId}/like/`;

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // Like the specified post
        return this.http.post(`${API_BASE_URL}/${likePostEndpoint}`, null, {
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

  // Unlike a post by sending a POST request with authentication
  unlikePost(postId: number): Observable<any> {
    const unlikePostEndpoint = `post/${postId}/unlike/`;

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // Unlike the specified post
        return this.http.post(`${API_BASE_URL}/${unlikePostEndpoint}`, null, {
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

  postLikersList(postId: number, page: number): Observable<any> {
    const postLikersEndpoint = `post/${postId}/likers/?page=${page}`;

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // Get the list of users who liked the specified post
        return this.http.get(`${API_BASE_URL}/${postLikersEndpoint}`, {
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
