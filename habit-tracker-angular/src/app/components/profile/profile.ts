import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthenticationService } from '../../services/auth';
import { HabitsService } from '../../services/habits';
import { OtpService } from '../../services/otp';

@Component({
  selector: 'app-profile',
  imports: [CommonModule, FormsModule],
  templateUrl: './profile.html',
  styleUrl: './profile.css'
})
export class Profile implements OnInit {
  user: any = null;
  habitCount = 0;
  completedToday = 0;
  weekCompletions = 0;
  completionRate = 0;
  recommendations: any[] = [];

  // Linking state
  showPasswordForm = false;
  newPassword = '';
  confirmNewPassword = '';
  linkError = '';
  linkSuccess = '';

  today = new Date().toISOString().split('T')[0];

  constructor(
    private authService: AuthenticationService,
    private habitsService: HabitsService,
    private otpService: OtpService,
    private router: Router
  ) {}

  ngOnInit() {
    this.user = this.authService.getCurrentUser();

    this.habitsService.getHabits().subscribe(habits => {
      const stats = this.habitsService.getStats(habits);
      this.habitCount      = stats.totalHabits;
      this.completedToday  = stats.todayCompleted;
      this.weekCompletions = stats.weekCompletions;
      this.completionRate  = stats.completionRate;
      this.recommendations = this.habitsService.getRecommendations(habits);
    });
  }

  get hasGoogle(): boolean {
    return this.authService.getLinkedProviders().includes('google.com');
  }

  get hasEmail(): boolean {
    return this.authService.getLinkedProviders().includes('password');
  }

  async linkGoogle() {
    this.linkError = '';
    try {
      await this.authService.linkCurrentWithGoogle();
      this.user = this.authService.getCurrentUser();
      this.linkSuccess = '✅ Cuenta de Google vinculada correctamente';
    } catch (error: any) {
      const code = error?.code || '';
      if (code === 'auth/credential-already-in-use') {
        this.linkError = 'Esta cuenta de Google ya está en uso por otro usuario';
      } else {
        this.linkError = `Error al vincular: ${code || error.message}`;
      }
    }
  }

  async linkEmailPassword() {
    this.linkError = '';
    this.linkSuccess = '';
    if (!this.newPassword) { this.linkError = 'Ingresa una contraseña'; return; }
    if (this.newPassword.length < 6) { this.linkError = 'Mínimo 6 caracteres'; return; }
    if (this.newPassword !== this.confirmNewPassword) { this.linkError = 'Las contraseñas no coinciden'; return; }
    try {
      await this.authService.linkCurrentWithEmail(this.newPassword);
      this.user = this.authService.getCurrentUser();
      this.linkSuccess = '✅ Contraseña establecida. Ahora puedes iniciar sesión con email/contraseña.';
      this.showPasswordForm = false;
      this.newPassword = '';
      this.confirmNewPassword = '';
    } catch (error: any) {
      const code = error?.code || '';
      if (code === 'auth/provider-already-linked') {
        this.linkError = 'Ya tienes contraseña vinculada';
      } else if (code === 'auth/weak-password') {
        this.linkError = 'Contraseña muy débil';
      } else {
        this.linkError = `Error: ${code || error.message}`;
      }
    }
  }

  getInitial(): string {
    return this.user?.displayName?.charAt(0)?.toUpperCase()
      || this.user?.email?.charAt(0)?.toUpperCase()
      || '?';
  }

  goToHabits() { this.router.navigate(['/habits']); }

  async logout() {
    this.otpService.clear();
    await this.authService.logout();
    this.router.navigate(['/login']);
  }
}
