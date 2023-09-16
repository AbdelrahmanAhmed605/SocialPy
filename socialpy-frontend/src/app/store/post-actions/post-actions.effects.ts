import { Injectable } from '@angular/core';

import { Actions, createEffect, ofType } from '@ngrx/effects';

import { of, EMPTY } from 'rxjs';
import { catchError, mergeMap, map } from 'rxjs/operators';

import { PostService } from 'src/app/api-services/post/post.service';
import * as PostActions from 'src/app/store/post-actions/post-actions.actions';

import { AuthService } from 'src/utilities/auth';

@Injectable()
export class PostActionsEffects {
  constructor(
    private actions$: Actions,
    private postService: PostService,
    private authService: AuthService
  ) {}

  // Effect middleware function to like a post when the 'likePost' action is called
  // The function calls the api to like the post and updates the selectLikedPostIds central selector state
  likePost$ = createEffect(() =>
    this.actions$.pipe(
      ofType(PostActions.likePost), // Listen for the 'likePost' action
      // using mergeMap instead of switchMap since mergeMap does not cancel previous requests when new actions of
      // the same type arrive.Instead, it processes all incoming actions concurrently. Meaning we can like multiple
      // posts without having them impact each other
      mergeMap((action) =>
        // Call the API to like the post
        this.postService.likePost(action.postId).pipe(
          // since mergeMap can allow multiple separate posts to be liked, we use map to handle each separate post
          map(() => PostActions.likePostSuccess({ postId: action.postId })), // Dispatch the action to add the post to the state variable
          catchError((error) => {
            // Log error
            console.error(error);
            // If error was due to authentication, call the likePostFailure action. 
            // This will be used in the component to alert the user to log in
            if (this.authService.isAuthenticationError(error)) {
              return of(PostActions.likePostFailure({ error }));
            } else {
              return EMPTY;
            }
          })
        )
      )
    )
  );

  // Effect middleware function to unlike a post when the 'unlikePost' action is called
  // The function calls the api to unlike the post and updates the selectLikedPostIds central selector state
  unlikePost$ = createEffect(() =>
    this.actions$.pipe(
      ofType(PostActions.unlikePost), // Listen for the 'likePost' action
      mergeMap((action) =>
        // Call the API to unlike the post
        this.postService.unlikePost(action.postId).pipe(
          // Dispatch the unlikePostSuccess action to remove the post from the state variable
          map(() => PostActions.unlikePostSuccess({ postId: action.postId })),
          catchError((error) => {
            // Log error
            console.error(error);
            // If error was due to authentication, call the unlikePostFailure action.
            // This will be used in the component to alert the user to log in
            if (this.authService.isAuthenticationError(error)) {
              return of(PostActions.unlikePostFailure({ error }));
            } else {
              return EMPTY;
            }
          })
        )
      )
    )
  );
}
