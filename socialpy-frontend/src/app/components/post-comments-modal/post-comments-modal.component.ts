import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ModalController, InfiniteScrollCustomEvent } from '@ionic/angular';

import { PostCommentsResponse } from 'src/app/interface-types/post-comments.model';

import { CommentService } from 'src/app/api-services/comment/comment.service';

import { faUser, faXmark } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-post-comments-modal',
  templateUrl: './post-comments-modal.component.html',
  styleUrls: ['./post-comments-modal.component.css'],
})
export class PostCommentsModalComponent implements OnInit {
  @Input() postId!: number;
  constructor(
    private router: Router,
    private commentService: CommentService,
    private modalCtrl: ModalController
  ) {}

  // Contains a list of comments for a post
  comments: any[] = [];
  currentCommentsPage = 1; // keep track of the current page of comments (for pagination)
  hasMoreCommentsData: boolean = false; // Keeps track if there is more paginated data

  // Font Awesome icons
  faXmark = faXmark;
  faUser = faUser;

  ngOnInit() {
    // Fetch the list of likers when the modal component is initialized
    this.fetchComments();
  }

  // Call the service api function to retrieve the comments for a specified post
  async fetchComments() {
    this.commentService
      .getPostComments(this.postId, this.currentCommentsPage)
      .subscribe({
        next: (data: PostCommentsResponse) => {
          this.hasMoreCommentsData = !!data.next; // Check if there is more paginated data
          this.comments = [...this.comments, ...data.results]; // Append new results to existing likers
        },
        error: (error) => {
          console.error('Error fetching comments:', error);
        },
      });
  }

  // Function used with ionic infinte scrolling to get the next page of paginated comments data
  loadMoreComments(event: Event) {
    // Increment the current page of paginated comments data
    this.currentCommentsPage++;

    // Call the service api with the updated page parameter
    this.fetchComments();

    setTimeout(() => {
      // Complete the infinite scroll event to indicate that loading is done
      (event as InfiniteScrollCustomEvent).target.complete();
      // Scroll back to the previous position
    }, 500);
  }

  // Function to close the modal display
  closeModal() {
    this.modalCtrl.dismiss();
  }

  // Redirect the user to the profile page associated with the user they are attempting to view
  goToUserProfilePage(userId: string) {
    this.closeModal();
    this.router.navigate(['/profile', userId]);
  }
}
