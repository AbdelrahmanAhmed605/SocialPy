import { Component, Input, OnInit, OnDestroy } from '@angular/core';

@Component({
  selector: 'app-single-post-modal',
  templateUrl: './single-post-modal.component.html',
  styleUrls: ['./single-post-modal.component.css'],
})
export class SinglePostModalComponent {
  @Input() postId!: number; // Input property to receive the ID of the post from the parent component
}
