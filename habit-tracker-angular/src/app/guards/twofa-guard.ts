import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { OtpService } from '../services/otp';
import { AuthenticationService } from '../services/auth';

export const twofaGuard: CanActivateFn = () => {
  const otpService  = inject(OtpService);
  const authService = inject(AuthenticationService);
  const router      = inject(Router);

  if (!authService.getCurrentUser()) {
    return router.createUrlTree(['/login']);
  }
  if (!otpService.isVerified()) {
    return router.createUrlTree(['/verify-2fa']);
  }
  return true;
};
