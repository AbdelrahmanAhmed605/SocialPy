import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { UserSignupComponent } from './user-signup/user-signup.component'
import { UserLoginComponent } from './user-login/user-login.component'

const routes: Routes = [
  { path: 'signup', component: UserSignupComponent },
  { path: 'login', component: UserLoginComponent },
  { path: '', component: HomeComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
