import { Injectable } from '@angular/core';

const EMAILJS_SERVICE_ID  = 'service_m721e5c';
const EMAILJS_TEMPLATE_ID = 'template_n64lzpb';
const EMAILJS_PUBLIC_KEY  = '0bgT5x8oKBlPRD6M4';

@Injectable({ providedIn: 'root' })
export class OtpService {

  private readonly SESSION_KEY  = 'ht_otp';
  private readonly VERIFIED_KEY = 'ht_2fa_verified';
  private readonly EXPIRY_MS    = 5 * 60 * 1000;

  async sendOtp(toEmail: string): Promise<void> {
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    const payload = { code, expiresAt: Date.now() + this.EXPIRY_MS };
    sessionStorage.setItem(this.SESSION_KEY, JSON.stringify(payload));

    console.log('[OTP] Enviando a:', toEmail, '| Código:', code);

    const body = {
      service_id:      EMAILJS_SERVICE_ID,
      template_id:     EMAILJS_TEMPLATE_ID,
      user_id:         EMAILJS_PUBLIC_KEY,
      template_params: {
        email:    toEmail,
        otp_code: code,
      }
    };

    const res = await fetch('https://api.emailjs.com/api/v1.0/email/send', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body)
    });

    const text = await res.text();
    console.log('[OTP] Respuesta EmailJS:', res.status, text);

    if (!res.ok) {
      throw new Error(`EmailJS error ${res.status}: ${text}`);
    }
  }

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

  isVerified(): boolean {
    return sessionStorage.getItem(this.VERIFIED_KEY) === 'true';
  }

  clear() {
    this.clearOtp();
    sessionStorage.removeItem(this.VERIFIED_KEY);
  }

  private clearOtp() {
    sessionStorage.removeItem(this.SESSION_KEY);
  }
}
