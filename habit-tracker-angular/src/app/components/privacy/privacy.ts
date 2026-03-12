import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-privacy',
  imports: [],
  templateUrl: './privacy.html',
  styleUrl: './privacy.css'
})
export class Privacy {
  currentDate = new Date().toLocaleDateString('es-MX');
  constructor(private router: Router) {}
  goBack() { this.router.navigate(['/habits']); }
}