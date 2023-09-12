import { Component, OnInit } from '@angular/core';

import { UserService } from '../api-services/user/user/user.service';
import AuthService from '../../utilities/auth';
import timeAgoFromString from 'src/utilities/dateTime';

import { faHeart, faComment } from '@fortawesome/free-regular-svg-icons';
import { faUser, faCircle } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent implements OnInit {
  faUser = faUser;
  faHeart = faHeart;
  faComment = faComment;
  faCircle = faCircle;

  feedData: any[] = []; // Property to store the feed data

  constructor(private userService: UserService) {}

  ngOnInit() {
    // Get the token from AuthService
    const token = AuthService.getToken();

    // Check if the user is logged in (token is available)
    if (token) {
      // Make the API call to get the user's feed data with the Authorization header
      this.userService.getUserFeed(token).subscribe(
        (response: any) => {
          console.log(response);
          response.results.forEach((result: any) => {
            // Calculate the formatted time difference and add it to the feedPost
            result.formattedTimeAgo = timeAgoFromString(result.created_at);
          });
          this.feedData = response.results; // Store the feed data in the property
        },
        (error: any) => {
          console.error('Error fetching user feed:', error);
          // Handle the error if needed
          console.log(error.error);
        }
      );
    } else {
      // Handle the case where the user is not logged in (token is not available)
      console.error('User is not logged in.');
    }
  }
}
