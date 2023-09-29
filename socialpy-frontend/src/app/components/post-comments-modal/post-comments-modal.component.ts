import { Component, Input, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import {
  ModalController,
  InfiniteScrollCustomEvent,
  IonContent,
  AlertController,
  Platform,
} from '@ionic/angular';

import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  faUser,
  faXmark,
  faCircle,
  faEllipsis,
  faTrash,
} from '@fortawesome/free-solid-svg-icons';

import { PostCommentsResponse } from 'src/app/interface-types/post-comments.model';
import { CommentService } from 'src/app/api-services/comment/comment.service';

import timeAgoFromString from 'src/utilities/dateTime';

@Component({
  selector: 'app-post-comments-modal',
  templateUrl: './post-comments-modal.component.html',
  styleUrls: ['./post-comments-modal.component.css'],
})
export class PostCommentsModalComponent implements OnInit, OnDestroy {
  // Input decorator to accept 'postId' from the parent component that calls this component
  @Input() postId!: number;
  // ViewChild decorator to get a reference to the IonContent element in the html
  // This allows us to programmatically control the IonContent element (such as using its scrolling methods)
  @ViewChild(IonContent) content!: IonContent;

  constructor(
    private router: Router, // Router service for routing functionality
    private commentService: CommentService, // Service for API calls
    private modalCtrl: ModalController, // for displaying modals
    private alertController: AlertController, // for displaying alerts
    private platform: Platform // for platform-specific functionality such as determining the width of the device viewing this component
  ) {}

  // Contains a list of comments for a post
  comments: any[] = [];
  currentCommentsPage = 1; // keep track of the current page of comments (for pagination)
  hasMoreCommentsData: boolean = false; // Keeps track if there is more paginated data

  userComment: string = ''; // Variable to store the user's new comment they are submitting
  submittingComment: boolean = false; // Keeps track if a comment is currently being submitted by the user

  private destroyed$ = new Subject<void>(); // Subject to track component destruction for subscription cleanup

  // Font Awesome icons
  faXmark = faXmark;
  faUser = faUser;
  faCircle = faCircle;
  faEllipsis = faEllipsis;
  faTrash = faTrash;

  ngOnInit() {
    // Fetch the list of likers when the modal component is initialized
    this.fetchComments();
  }

  // Call the service api function to retrieve the comments for a specified post
  async fetchComments() {
    this.commentService
      .getPostComments(this.postId, this.currentCommentsPage)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: (data: PostCommentsResponse) => {
          this.hasMoreCommentsData = !!data.next; // Check if there is more paginated data
          this.comments = [
            ...this.comments,
            ...data.results.map((comment) => ({
              ...comment,
              // add field to indicate when comment was made relative to current time
              formattedTimeAgo: timeAgoFromString(comment.created_at),
            })),
          ]; // Append new results to existing likers
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

  // Function to handle keydown event on the textarea
  onTextareaKeyDown(event: KeyboardEvent) {
    // The enter key is now used to submit the post comment.
    // shift+enter is used to create a new line
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.submitComment();
    }
  }

  // Function to scroll the users viewwindow to the top of the component
  scrollToTop() {
    // Passing a duration to the method makes it so the scroll slowly
    // goes to the top instead of instantly
    this.content.scrollToTop(500);
  }

  // Function to submit a new comment
  async submitComment() {
    // Prevent submitting empty comments
    if (this.userComment.trim() === '') {
      return;
    }

    // Disable the submit button while submitting
    this.submittingComment = true;

    // Call the createComment service to post the comment
    this.commentService
      .createComment(this.postId, this.userComment)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: (newCommentData) => {
          // add field to indicate when comment was made relative to current time
          newCommentData.formattedTimeAgo = timeAgoFromString(
            newCommentData.created_at
          );

          // Add the new comment to the comments array
          this.comments.unshift(newCommentData);

          // Enable the submit button after successful submission
          this.submittingComment = false;

          // Scroll to the top so the user can see their new comment
          this.scrollToTop();

          // Clear the comment input field
          this.userComment = '';
        },
        error: (error) => {
          console.error('Error fetching comments:', error);

          // Enable the submit button in case of an error
          this.submittingComment = false;
        },
      });
  }

  // Check if the screen width is greater than 768px
  isLargeScreen(): boolean {
    return this.platform.width() > 768;
  }

  // Function to delete a comment with a specified commentId
  async deleteComment(commentId: number) {
    // Call the commentService to delete the comment
    this.commentService
      .deleteComment(commentId)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: () => {
          // After comment is deleted successfully, remove it from the comments state array
          const index = this.comments.findIndex(
            (comment) => comment.id === commentId
          );
          if (index !== -1) {
            this.comments.splice(index, 1);
          }
        },
        error: (error) => {
          console.error('Error deleting comment:', error);
        },
      });
  }

  // Open an ionic alert displaying buttons of actions to perform on a specific comment by passing the commentId
  async openCommentActionsAlert(commentId: number) {
    const alert = await this.alertController.create({
      cssClass: 'delete-comment-alert',
      buttons: [
        // Delete button to delete the comment associated with the alert
        {
          text: 'Delete',
          cssClass: 'delete-button',
          handler: () => {
            this.deleteComment(commentId);
          },
        },
        // Cancel button to close the alert
        {
          text: 'Cancel',
          cssClass: 'cancel-button',
          handler: () => {
            alert.dismiss();
          },
        },
      ],
    });

    await alert.present();
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

  ngOnDestroy(): void {
    // Complete the `destroyed$` Subject to signal unsubscription to any ongoing observables
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
