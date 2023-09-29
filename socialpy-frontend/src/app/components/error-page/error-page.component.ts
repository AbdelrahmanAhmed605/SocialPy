import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-error-page',
  templateUrl: './error-page.component.html',
  styleUrls: ['./error-page.component.css'],
})
export class ErrorPageComponent implements OnInit {
  @Input() error: any;

  constructor(private router: Router) {}

  ngOnInit(): void {
    if (this.error) {
      console.error(this.error);
    }
  }

  // Define a function to get the error message based on the status code
  getErrorMessage(status: number): string {
    switch (status) {
      case 401:
        return "Looks like you shouldn't be here...or maybe you should, what do I know. Let's log you in and see.";
      case 404:
        return "Looks like the page you're looking for is not found. It's probably time to head back...";
      case 500:
        return "Looks like there's a server issue. As you can see by this accurate portrayal of me, I am trying my best to get it fixed. For now lets just head back to the home page";
      default:
        return "Looks like something went wrong. Let's get you back to the site...you've been stranded out here for too long.";
    }
  }

  getErrorImage(status: number): string {
    switch (status) {
      case 401:
        return 'https://coreldrawdesign.com/resources/previews/preview-error-401-access-denied-vector-creative-1612798070.jpg';
      case 404:
        return 'https://th.bing.com/th/id/R.61506032fe0cd9d2cec6b605e4542bde?rik=E%2b9ISKTojEJt1Q&riu=http%3a%2f%2fi0.kym-cdn.com%2fphotos%2fimages%2foriginal%2f000%2f241%2f713%2f0fb.gif&ehk=Q0gx3oP49JX9t0%2bh%2fXKchAqYynaxFQKAZvn1GuDmARw%3d&risl=&pid=ImgRaw&r=0';
      case 500:
        return 'https://media.giphy.com/media/AEcZfXZZNCcQU/200.gif';
      default:
        return 'https://media.istockphoto.com/vectors/cartoon-of-politician-or-businessman-standing-depressed-on-sinking-vector-id1053225534?k=6&m=1053225534&s=170667a&w=0&h=qT52raPwlduFfDucMV2BRQ19JLjsf0hKfUA4_o4bbKs=';
    }
  }

  // Navigate to the appropriate page based on the status
  redirectButton(status: number): void {
    if (status === 401) {
      // Redirect to the login page for authentication error
      this.router.navigate(['/login']);
    } else {
      // Redirect to the home page for other errors
      this.router.navigate(['/']);
    }
  }
}
