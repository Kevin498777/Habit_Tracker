import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthenticationService } from '../../services/auth';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  imports: [FormsModule, CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {
  email = '';
  password = '';
  rememberMe = false;
  errorMessage = '';

  // Estado de linking: cuando Google detecta cuenta de email/password existente
  needsLinking = false;
  linkingEmail = '';
  linkingPassword = '';
  linkingError = '';

  constructor(private authService: AuthenticationService, private router: Router) {}

  async onLogin() {
    this.errorMessage = '';
    if (!this.email.trim()) { this.errorMessage = 'Ingresa tu correo electrónico'; return; }
    if (!this.password.trim()) { this.errorMessage = 'Ingresa tu contraseña'; return; }
    try {
      await this.authService.login(this.email.trim(), this.password);
      this.router.navigate(['/verify-2fa']);
    } catch (error: any) {
      const code = error?.code || '';
      if (code === 'auth/invalid-credential' || code === 'auth/wrong-password' || code === 'auth/user-not-found') {
        this.errorMessage = 'Correo o contraseña incorrectos. Si te registraste con Google, usa el botón de Google.';
      } else if (code === 'auth/invalid-email') {
        this.errorMessage = 'El formato del correo no es válido';
      } else if (code === 'auth/too-many-requests') {
        this.errorMessage = 'Demasiados intentos. Espera unos minutos';
      } else {
        this.errorMessage = `Error: ${code || error.message}`;
      }
    }
  }

  async onGoogleLogin() {
    this.errorMessage = '';
    try {
      await this.authService.loginWithGoogle();
      this.router.navigate(['/verify-2fa']);
    } catch (error: any) {
      // El correo ya existe con email/password → mostrar panel de linking
      if (error.code === 'auth/link-required') {
        this.needsLinking = true;
        this.linkingEmail = error.email || '';
        this.linkingPassword = '';
        this.linkingError = '';
      } else {
        this.errorMessage = 'Error al iniciar sesión con Google';
      }
    }
  }

  /** El usuario ingresa su contraseña para vincular Google a su cuenta existente */
  async onLinkAccounts() {
    this.linkingError = '';
    if (!this.linkingPassword) { this.linkingError = 'Ingresa tu contraseña'; return; }
    try {
      await this.authService.linkEmailWithPendingGoogle(this.linkingPassword);
      this.needsLinking = false;
      this.router.navigate(['/verify-2fa']);
    } catch (error: any) {
      const code = error?.code || '';
      if (code === 'auth/wrong-password' || code === 'auth/invalid-credential') {
        this.linkingError = 'Contraseña incorrecta';
      } else {
        this.linkingError = `Error al vincular: ${code || error.message}`;
      }
    }
  }

  cancelLinking() {
    this.needsLinking = false;
    this.linkingEmail = '';
    this.linkingPassword = '';
    this.linkingError = '';
    this.authService.pendingGoogleCredential = null;
    this.authService.pendingEmail = '';
  }

  goToRegister() { this.router.navigate(['/register']); }
}
