import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-terms',
  imports: [],
  templateUrl: './terms.html',
  styleUrl: './terms.css'
})
export class Terms {
  currentDate = new Date().toLocaleDateString('es-MX');
  constructor(private router: Router) {}
  goBack() { this.router.navigate(['/habits']); }
}