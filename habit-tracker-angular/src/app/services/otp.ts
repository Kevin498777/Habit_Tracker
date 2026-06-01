import { Injectable } from '@angular/core';
import emailjs from '@emailjs/browser';

const EMAILJS_SERVICE_ID  = 'service_m721e5c';
const EMAILJS_TEMPLATE_ID = 'template_n64lzpb';
const EMAILJS_PUBLIC_KEY  = '0bgT5x8oKBlPRD6M4';

@Injectable({ providedIn: 'root' })
export class OtpService {

  private readonly SESSION_KEY  = 'ht_otp';
  private readonly VERIFIED_KEY = 'ht_2fa_verified';
  private readonly EXPIRY_MS    = 5 * 60 * 1000; // 5 minutos

  constructor() {
    emailjs.init(EMAILJS_PUBLIC_KEY);
  }

  /** Genera un OTP de 6 dígitos, lo guarda con expiración y lo envía al correo */
  async sendOtp(toEmail: string): Promise<void> {
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    const payload = { code, expiresAt: Date.now() + this.EXPIRY_MS };
    sessionStorage.setItem(this.SESSION_KEY, JSON.stringify(payload));

    await emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, {
      to_email: toEmail,
      otp_code: code,
    });
  }

  /** Verifica el código ingresado. Retorna 'ok', 'expired' o 'invalid' */
  verifyOtp(input: string): 'ok' | 'expired' | 'invalid' {
    const raw = sessionStorage.getItem(this.SESSION_KEY);
    if (!raw) return 'invalid';

    const { code, expiresAt } = JSON.parse(raw);

    if (Date.now() > expiresAt) {
      this.clearOtp();
      return 'expired';
    }
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

  /** Limpia todo al hacer logout */
  clear() {
    this.clearOtp();
    sessionStorage.removeItem(this.VERIFIED_KEY);
  }

  private clearOtp() {
    sessionStorage.removeItem(this.SESSION_KEY);
  }
}
