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
    this.errorMessage = '';
    if (!this.email.trim())    { this.errorMessage = 'Ingresa tu correo electrónico'; return; }
    if (!this.password)        { this.errorMessage = 'Ingresa una contraseña'; return; }
    if (!this.acceptedTerms)   { this.errorMessage = 'Debes aceptar los términos y condiciones'; return; }
    if (this.password !== this.confirmPassword) { this.errorMessage = 'Las contraseñas no coinciden'; return; }
    if (this.password.length < 6) { this.errorMessage = 'La contraseña debe tener al menos 6 caracteres'; return; }
    try {
      await this.authService.register(this.email.trim(), this.password);
      this.router.navigate(['/verify-2fa']); // flujo correcto: registro → 2FA → habits
    } catch (error: any) {
      const code = error?.code || '';
      if (code === 'auth/email-already-in-use') {
        this.errorMessage = 'Este correo ya tiene una cuenta. Si te registraste con Google, inicia sesión con el botón de Google.';
      } else if (code === 'auth/invalid-email') {
        this.errorMessage = 'El formato del correo no es válido';
      } else if (code === 'auth/weak-password') {
        this.errorMessage = 'La contraseña es muy débil, usa al menos 6 caracteres';
      } else if (code === 'auth/operation-not-allowed') {
        this.errorMessage = 'Registro por email no habilitado — actívalo en Firebase Console → Authentication → Sign-in method';
      } else {
        this.errorMessage = `Error: ${code || error.message}`;
      }
    }
  }

  goToLogin()  { this.router.navigate(['/login']); }
  goToTerms()  { this.router.navigate(['/terms']); }
}
