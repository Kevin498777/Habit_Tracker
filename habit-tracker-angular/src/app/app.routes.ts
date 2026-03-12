import { Routes } from '@angular/router';
import { Login } from './components/login/login';
import { Register } from './components/register/register';
import { Habits } from './components/habits/habits';
import { Profile } from './components/profile/profile';
import { Privacy } from './components/privacy/privacy';
import { Terms } from './components/terms/terms';
import { Contact } from './components/contact/contact';
import { authGuard } from './guards/auth-guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  { path: 'habits', component: Habits, canActivate: [authGuard] },
  { path: 'profile', component: Profile, canActivate: [authGuard] },
  { path: 'privacy', component: Privacy },
  { path: 'terms', component: Terms },
  { path: 'contact', component: Contact },
];