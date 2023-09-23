import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ModalController } from '@ionic/angular';

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

  // Font Awesome icons
  faXmark = faXmark;
  faUser = faUser;

  ngOnInit() {
    // Fetch the list of likers when the modal component is initialized
    this.fetchComments();
  }

  // Call the service api function to retrieve the comments for a specified post
  async fetchComments() {
    this.commentService.getPostComments(this.postId).subscribe({
      next: (data: PostCommentsResponse) => {
        console.log(data);
        this.comments = [...this.comments, ...data.results]; // Append new results to existing likers
      },
      error: (error) => {
        // Handle any errors here
        console.error('Error fetching comments:', error);
      },
    });
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
