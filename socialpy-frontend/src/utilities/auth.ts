class AuthService {
  // Get the token from localStorage
  getToken(): string | null {
    return localStorage.getItem("id_token");
  }

  // Perform login by storing the token in localStorage
  login(idToken: string): void {
    localStorage.setItem("id_token", idToken);
  }

  // Check if the user is logged in
  loggedIn(): boolean {
    const token = this.getToken();
    return !!token;
  }

  // Perform logout by removing the token from localStorage and redirecting to the main page
  logout(): void {
    localStorage.removeItem("id_token");
    window.location.assign("/");
  }
}

export default new AuthService();
