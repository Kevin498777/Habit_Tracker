import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { OtpService } from '../../services/otp';
import { AuthenticationService } from '../../services/auth';

@Component({
  selector: 'app-verify-2fa',
  imports: [FormsModule, CommonModule],
  templateUrl: './verify-2fa.html',
  styleUrl: './verify-2fa.css'
})
export class Verify2fa implements OnInit {
  otpInput = '';
  errorMessage = '';
  timeLeft = 300; // segundos
  timerInterval: any;

  // Solo para entorno de prueba: muestra el código en pantalla
  shownCode = '';
  email = '';

  constructor(
    private otpService: OtpService,
    private authService: AuthenticationService,
    private router: Router
  ) {}

  ngOnInit() {
    // Si ya verificó en esta sesión, pasar directo
    if (this.otpService.isVerified()) {
      this.router.navigate(['/habits']);
      return;
    }
    // Si no viene de un login activo, redirigir
    const user = this.authService.getCurrentUser();
    if (!user) { this.router.navigate(['/login']); return; }

    this.email = user.email || '';
    this.shownCode = this.otpService.generateOtp();
    this.startTimer();
  }

  startTimer() {
    this.timerInterval = setInterval(() => {
      this.timeLeft--;
      if (this.timeLeft <= 0) {
        clearInterval(this.timerInterval);
        this.errorMessage = 'El código ha expirado. Genera uno nuevo.';
        this.shownCode = '';
      }
    }, 1000);
  }

  regenerate() {
    clearInterval(this.timerInterval);
    this.timeLeft = 300;
    this.otpInput = '';
    this.errorMessage = '';
    this.shownCode = this.otpService.generateOtp();
    this.startTimer();
  }

  verify() {
    const result = this.otpService.verifyOtp(this.otpInput);
    if (result === 'ok') {
      clearInterval(this.timerInterval);
      this.router.navigate(['/habits']);
    } else if (result === 'expired') {
      this.errorMessage = 'El código ha expirado. Genera uno nuevo.';
      this.shownCode = '';
    } else {
      this.errorMessage = 'Código incorrecto. Inténtalo de nuevo.';
    }
  }

  async cancelLogin() {
    clearInterval(this.timerInterval);
    await this.authService.logout();
    this.otpService.clear();
    this.router.navigate(['/login']);
  }

  get formattedTime(): string {
    const m = Math.floor(this.timeLeft / 60).toString().padStart(2, '0');
    const s = (this.timeLeft % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  ngOnDestroy() {
    clearInterval(this.timerInterval);
  }
}
