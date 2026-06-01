import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-terms',
  imports: [CommonModule],
  templateUrl: './terms.html',
  styleUrl: './terms.css'
})
export class Terms {
  currentDate = new Date().toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' });
  docId = new Date().toISOString().split('T')[0].replace(/-/g, '');

  constructor(private router: Router) {}

  goBack()       { this.router.navigate(['/habits']); }
  goToPrivacy()  { this.router.navigate(['/privacy']); }
  goToRegister() { this.router.navigate(['/register']); }
}