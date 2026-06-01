import { Injectable } from '@angular/core';
import {
  Auth, signInWithEmailAndPassword, createUserWithEmailAndPassword,
  signOut, user, GoogleAuthProvider, signInWithPopup,
  linkWithCredential, linkWithPopup, EmailAuthProvider,
  OAuthCredential
} from '@angular/fire/auth';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthenticationService {

  user$: Observable<any>;

  // Almacena temporalmente credencial de Google pendiente de vincular
  pendingGoogleCredential: OAuthCredential | null = null;
  pendingEmail = '';

  constructor(private auth: Auth) {
    this.user$ = user(this.auth);
  }

  register(email: string, password: string) {
    return createUserWithEmailAndPassword(this.auth, email, password);
  }

  login(email: string, password: string) {
    return signInWithEmailAndPassword(this.auth, email, password);
  }

  async loginWithGoogle() {
    const provider = new GoogleAuthProvider();
    try {
      return await signInWithPopup(this.auth, provider);
    } catch (error: any) {
      // El correo ya existe con otro proveedor (email/password)
      if (error.code === 'auth/account-exists-with-different-credential') {
        this.pendingGoogleCredential = GoogleAuthProvider.credentialFromError(error);
        this.pendingEmail = error.customData?.email || '';
        throw { code: 'auth/link-required', email: this.pendingEmail };
      }
      throw error;
    }
  }

  /** Vincula cuenta existente de email/password con Google pendiente */
  async linkEmailWithPendingGoogle(password: string) {
    if (!this.pendingGoogleCredential || !this.pendingEmail) {
      throw new Error('No hay credencial de Google pendiente');
    }
    const result = await signInWithEmailAndPassword(this.auth, this.pendingEmail, password);
    await linkWithCredential(result.user, this.pendingGoogleCredential);
    this.pendingGoogleCredential = null;
    this.pendingEmail = '';
    return result;
  }

  /** Vincula Google a la cuenta actual (desde perfil) */
  async linkCurrentWithGoogle() {
    const provider = new GoogleAuthProvider();
    return linkWithPopup(this.auth.currentUser!, provider);
  }

  /** Vincula email/password a la cuenta actual de Google (desde perfil) */
  async linkCurrentWithEmail(password: string) {
    const user = this.auth.currentUser;
    if (!user?.email) throw new Error('No hay usuario autenticado');
    const credential = EmailAuthProvider.credential(user.email, password);
    return linkWithCredential(user, credential);
  }

  /** Proveedores vinculados al usuario actual */
  getLinkedProviders(): string[] {
    return this.auth.currentUser?.providerData.map(p => p.providerId) || [];
  }

  logout() {
    return signOut(this.auth);
  }

  getCurrentUser() {
    return this.auth.currentUser;
  }
}
