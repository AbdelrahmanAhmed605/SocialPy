import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { ModalController } from '@ionic/angular';

import { PostLikersResponse } from 'src/app/interface-types/post-likers';

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

  likers: any[] = [];
  // Font Awesome icons
  faXmark = faXmark;
  faUser = faUser;

  ngOnInit() {
    // Fetch the list of likers when the modal component is initialized
    this.fetchLikers();
  }

  // Call the service api function to retrieve the list of users who liked a post
  async fetchLikers() {
    this.postService.postLikersList(this.postId).subscribe({
      next: (data: PostLikersResponse) => {
        this.likers = data.results;
      },
      error: (error) => {
        // Handle any errors here
        console.error('Error fetching likers:', error);
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

  ngOnDestroy(): void {
    this.closeModal();
  }
}
