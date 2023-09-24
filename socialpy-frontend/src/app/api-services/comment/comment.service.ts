import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { Observable, throwError } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';

import { API_BASE_URL } from '../api.config';
import { AuthService } from 'src/utilities/auth';

@Injectable({
  providedIn: 'root',
})
export class CommentService {
  constructor(private http: HttpClient, private authService: AuthService) {}

  // API call to get comments for a specified post
  getPostComments(postId: number, page: number): Observable<any> {
    const postCommentsEndpoint = `comments/post/${postId}/?page=${page}`;

    return this.authService.handleAuthenticationToken().pipe(
      switchMap((token) => {
        // Set the headers with the Authorization token
        const headers = new HttpHeaders({
          Authorization: `Token ${token}`,
        });

        // call API to get comments for the post
        return this.http.get(`${API_BASE_URL}/${postCommentsEndpoint}`, {
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
