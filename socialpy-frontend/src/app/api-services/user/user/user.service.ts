import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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
}
