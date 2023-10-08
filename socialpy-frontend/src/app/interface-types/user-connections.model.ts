// Contains the structure of the returned data from the API when fetching a users connections (their followers or following)
export interface UserConnectionsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Array<{
    // Array of user models
    id: number;
    username: string;
    profile_picture: string | null;
    // determines the follow status of the requesting user (user making the api call on the front-end) to the user in the api result array
    requesting_user_follow_status: string | boolean;
  }>;
}
