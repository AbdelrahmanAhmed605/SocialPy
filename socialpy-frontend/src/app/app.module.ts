import { NgModule } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';

import { HttpClientModule } from '@angular/common/http';
import { AppRoutingModule } from './app-routing.module';

import { StoreModule } from '@ngrx/store';
import { EffectsModule } from '@ngrx/effects';
import { reducers } from './store/app.state'; 

import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { IonicModule } from '@ionic/angular';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AuthService } from 'src/utilities/auth';
import { UserService } from './api-services/user/user.service';
import { PostService } from './api-services/post/post.service';

import { AppComponent } from './app.component';
import { HomeComponent } from './components/home/home.component';
import { UserSignupComponent } from './components/user-signup/user-signup.component';
import { UserLoginComponent } from './components/user-login/user-login.component';
import { UserProfileComponent } from './components/user-profile/user-profile.component';
import { ErrorPageComponent } from './components/error-page/error-page.component';
import { LoadingPageComponent } from './components/loading-page/loading-page.component';

import { UserFeedEffects } from './store/user-feed/user-feed.effects';
import { PostActionsEffects } from './store/post-actions/post-actions.effects';
import { AppThemeEffects } from './store/app-theme/app-theme.effects';

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    UserSignupComponent,
    UserLoginComponent,
    UserProfileComponent,
    ErrorPageComponent,
    LoadingPageComponent,
  ],
  imports: [
    HttpClientModule,
    AppRoutingModule,

    BrowserModule,
    BrowserAnimationsModule,

    IonicModule.forRoot(),
    FontAwesomeModule,

    FormsModule,
    ReactiveFormsModule,
    StoreModule.forRoot(reducers),
    EffectsModule.forRoot([
      UserFeedEffects,
      PostActionsEffects,
      AppThemeEffects,
    ]),
  ],
  providers: [AuthService, UserService, PostService],
  bootstrap: [AppComponent],
})
export class AppModule {}
