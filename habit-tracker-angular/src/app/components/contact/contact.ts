import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-contact',
  imports: [FormsModule, CommonModule],
  templateUrl: './contact.html',
  styleUrl: './contact.css'
})
export class Contact {
  name = '';
  email = '';
  message = '';
  sent = false;

  constructor(private router: Router) {}

  sendMessage() {
    if (!this.name || !this.email || !this.message) return;
    this.sent = true;
    this.name = '';
    this.email = '';
    this.message = '';
  }

  goBack() { this.router.navigate(['/habits']); }
}