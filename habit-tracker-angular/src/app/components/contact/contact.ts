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
  subject = '';
  message = '';
  privacyAccepted = false;
  sent = false;
  formError = '';

  constructor(private router: Router) {}

  sendMessage() {
    this.formError = '';
    if (!this.name || !this.email || !this.subject || !this.message) {
      this.formError = 'Por favor completa todos los campos.';
      return;
    }
    if (!this.privacyAccepted) {
      this.formError = 'Debes aceptar la Política de Privacidad.';
      return;
    }
    this.sent = true;
    this.name = ''; this.email = ''; this.subject = '';
    this.message = ''; this.privacyAccepted = false;
  }

  goBack()      { this.router.navigate(['/habits']); }
  goToPrivacy() { this.router.navigate(['/privacy']); }
  goToTerms()   { this.router.navigate(['/terms']); }
}
