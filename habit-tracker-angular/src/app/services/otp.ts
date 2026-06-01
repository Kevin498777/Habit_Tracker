import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class OtpService {

  private readonly SESSION_KEY = 'ht_otp';
  private readonly VERIFIED_KEY = 'ht_2fa_verified';
  private readonly EXPIRY_MS = 5 * 60 * 1000; // 5 minutos

  /** Genera un código OTP de 6 dígitos, lo guarda en sessionStorage con expiración */
  generateOtp(): string {
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    const payload = { code, expiresAt: Date.now() + this.EXPIRY_MS };
    sessionStorage.setItem(this.SESSION_KEY, JSON.stringify(payload));
    return code;
  }

  /** Verifica el código ingresado. Retorna 'ok', 'expired' o 'invalid' */
  verifyOtp(input: string): 'ok' | 'expired' | 'invalid' {
    const raw = sessionStorage.getItem(this.SESSION_KEY);
    if (!raw) return 'invalid';
    const { code, expiresAt } = JSON.parse(raw);
    if (Date.now() > expiresAt) { this.clearOtp(); return 'expired'; }
    if (input.trim() === code) {
      this.clearOtp();
      sessionStorage.setItem(this.VERIFIED_KEY, 'true');
      return 'ok';
    }
    return 'invalid';
  }

  /** ¿Ya completó el 2FA en esta sesión? */
  isVerified(): boolean {
    return sessionStorage.getItem(this.VERIFIED_KEY) === 'true';
  }

  /** Limpia la verificación al hacer logout */
  clear() {
    this.clearOtp();
    sessionStorage.removeItem(this.VERIFIED_KEY);
  }

  private clearOtp() {
    sessionStorage.removeItem(this.SESSION_KEY);
  }
}
