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

  customize() {
    // Guarda preferencia parcial y redirige a privacy para configurar
    localStorage.setItem('cookie_consent', 'custom');
    this.showBanner = false;
    this.router.navigate(['/privacy']);
  }

  goToPolicy() {
    this.router.navigate(['/privacy']);
  }
}
