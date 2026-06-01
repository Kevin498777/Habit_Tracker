import { Routes } from '@angular/router';
import { Login } from './components/login/login';
import { Register } from './components/register/register';
import { Habits } from './components/habits/habits';
import { Profile } from './components/profile/profile';
import { Privacy } from './components/privacy/privacy';
import { Terms } from './components/terms/terms';
import { Contact } from './components/contact/contact';
import { Calendar } from './components/calendar/calendar';
import { Verify2fa } from './components/verify-2fa/verify-2fa';
import { authGuard } from './guards/auth-guard';
import { twofaGuard } from './guards/twofa-guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  { path: 'verify-2fa', component: Verify2fa, canActivate: [authGuard] },
  { path: 'habits',   component: Habits,   canActivate: [authGuard, twofaGuard] },
  { path: 'calendar', component: Calendar, canActivate: [authGuard, twofaGuard] },
  { path: 'profile',  component: Profile,  canActivate: [authGuard, twofaGuard] },
  { path: 'privacy',  component: Privacy },
  { path: 'terms',    component: Terms },
  { path: 'contact',  component: Contact },
];