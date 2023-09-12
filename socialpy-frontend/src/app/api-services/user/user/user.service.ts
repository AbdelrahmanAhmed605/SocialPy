import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root', // This makes the service a singleton across the application.
})
export class UserService {
  private apiUrl = 'http://127.0.0.1:8000/api/users/';

  constructor(private http: HttpClient) {}

  createUser(userData: any): Observable<any> {
    // Make the POST request with userData
    return this.http.post(this.apiUrl, userData, { withCredentials: true });
  }

  loginUser(userData: any): Observable<any> {
    // Make a POST request to the login route
    const loginUrl = 'http://127.0.0.1:8000/api/login/';
    return this.http.post(loginUrl, userData, { withCredentials: true });
  }

  getUserFeed(token: string): Observable<any> {
    const feedUrl = 'http://127.0.0.1:8000/api/feed';

    // Set the headers with the Authorization token
    const headers = new HttpHeaders({
      Authorization: `Token ${token}`,
    });

    return this.http.get(feedUrl, { headers, withCredentials: true });
  }
}
