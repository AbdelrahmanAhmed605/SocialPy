import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { InfiniteScrollCustomEvent, ModalController } from '@ionic/angular';

import { PostLikersResponse } from 'src/app/interface-types/post-likers.model';

import { PostService } from 'src/app/api-services/post/post.service';

import { faUser, faXmark } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-post-likers-modal',
  templateUrl: './post-likers-modal.component.html',
  styleUrls: ['./post-likers-modal.component.css'],
})
export class PostLikersModalComponent implements OnInit, OnDestroy {
  @Input() postId!: number;
  constructor(
    private router: Router,
    private modalCtrl: ModalController,
    private postService: PostService
  ) {}

  // Contains a list of users who liked a post
  likers: any[] = [];
  currentUserLikersPage = 1; // keep track of the current page of user likers (for pagination)
  hasMoreUserLikersData: boolean = false; // Keeps track if there is more paginated data

  // Font Awesome icons
  faXmark = faXmark;
  faUser = faUser;

  ngOnInit() {
    // Fetch the list of likers when the modal component is initialized
    this.fetchLikers();
  }

  // Call the service api function to retrieve the list of users who liked a post
  async fetchLikers() {
    this.postService.postLikersList(this.postId, this.currentUserLikersPage).subscribe({
      next: (data: PostLikersResponse) => {
        this.hasMoreUserLikersData = !!data.next; // Check if there is more paginated data
        this.likers = [...this.likers, ...data.results]; // Append new results to existing likers
      },
      error: (error) => {
        // Handle any errors here
        console.error('Error fetching likers:', error);
      },
    });
  }

  loadMoreLikers(event: Event) {
    // Increment the current page of paginated user likers data
    this.currentUserLikersPage++;

    // Call the service api with the updated page parameter
    this.fetchLikers();

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

  ngOnDestroy(): void {
    this.closeModal();
  }
}
