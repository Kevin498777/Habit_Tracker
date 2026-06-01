import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthenticationService } from '../../services/auth';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-register',
  imports: [FormsModule, CommonModule],
  templateUrl: './register.html',
  styleUrl: './register.css'
})
export class Register {
  username = '';
  email = '';
  password = '';
  confirmPassword = '';
  acceptedTerms = false;
  errorMessage = '';

  constructor(private authService: AuthenticationService, private router: Router) {}

  async onRegister() {
    if (!this.acceptedTerms) {
      this.errorMessage = 'Debes aceptar los términos y condiciones';
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Las contraseñas no coinciden';
      return;
    }
    if (this.password.length < 6) {
      this.errorMessage = 'La contraseña debe tener al menos 6 caracteres';
      return;
    }
    try {
      await this.authService.register(this.email, this.password);
      this.router.navigate(['/habits']);
    } catch (error: any) {
      this.errorMessage = 'Error al registrarse, intenta con otro correo';
    }
  }

  goToLogin()  { this.router.navigate(['/login']); }
  goToTerms()  { this.router.navigate(['/terms']); }
}
