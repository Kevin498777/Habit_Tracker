import { Component, OnInit, HostListener } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthenticationService } from '../../services/auth';

@Component({
  selector: 'app-navbar',
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css'
})
export class Navbar implements OnInit {
  user: any = null;
  isMenuOpen = false;
  isDropdownOpen = false;

  constructor(
    private authService: AuthenticationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.user = this.authService.getCurrentUser();
    // Re-check on navigation
    this.router.events.subscribe(() => {
      this.user = this.authService.getCurrentUser();
      this.isMenuOpen = false;
      this.isDropdownOpen = false;
    });
  }

  get isLoggedIn(): boolean {
    return !!this.user;
  }

  get displayName(): string {
    return this.user?.displayName || this.user?.email?.split('@')[0] || 'Usuario';
  }

  get initial(): string {
    return (this.user?.displayName || this.user?.email || '?').charAt(0).toUpperCase();
  }

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
  }

  toggleDropdown() {
    this.isDropdownOpen = !this.isDropdownOpen;
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.dropdown-wrapper')) {
      this.isDropdownOpen = false;
    }
  }

  navigate(path: string) {
    this.router.navigate([path]);
    this.isMenuOpen = false;
    this.isDropdownOpen = false;
  }

  async logout() {
    await this.authService.logout();
    this.router.navigate(['/login']);
  }
}
