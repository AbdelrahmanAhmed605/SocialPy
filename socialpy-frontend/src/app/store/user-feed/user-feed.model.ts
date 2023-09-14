// Represents the structure of a post object received from the API.
export interface Post {
  comment_count: number;
  content: string;
  created_at: string;
  formattedTimeAgo: string;
  hashtags: string[];
  id: number;
  like_count: number;
  liked_by_user: boolean;
  media: string;
  updated_at: string;
  user: {
    id: number;
    username: string;
    profile_picture: string | null;
  };
  visibility: string;
}
