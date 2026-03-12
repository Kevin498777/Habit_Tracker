import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-cookies-banner',
  imports: [CommonModule],
  templateUrl: './cookies-banner.html',
  styleUrl: './cookies-banner.css'
})
export class CookiesBanner implements OnInit {
  showBanner = false;

  constructor(private router: Router) {}

  ngOnInit() {
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) this.showBanner = true;
  }

  acceptAll() {
    localStorage.setItem('cookie_consent', 'all');
    this.showBanner = false;
  }

  acceptEssential() {
    localStorage.setItem('cookie_consent', 'essential');
    this.showBanner = false;
  }

  goToPolicy() {
    this.router.navigate(['/privacy']);
  }
}