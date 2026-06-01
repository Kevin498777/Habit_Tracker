import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-privacy',
  imports: [CommonModule],
  templateUrl: './privacy.html',
  styleUrl: './privacy.css'
})
export class Privacy {
  currentDate = new Date().toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' });
  docId = new Date().toISOString().split('T')[0].replace(/-/g, '');

  rights = [
    { icon: '📋', title: 'Derecho de Acceso', body: 'Puedes solicitar una copia de los datos personales que tenemos sobre ti.', open: true },
    { icon: '✏️', title: 'Derecho de Rectificación', body: 'Puedes solicitar la corrección de datos inexactos o incompletos.', open: false },
    { icon: '🗑️', title: 'Derecho de Supresión', body: 'Puedes solicitar la eliminación de tus datos personales ("derecho al olvido").', open: false },
    { icon: '⏸️', title: 'Derecho de Oposición', body: 'Puedes oponerte al tratamiento de tus datos en determinadas circunstancias.', open: false },
    { icon: '📤', title: 'Derecho de Portabilidad', body: 'Puedes recibir tus datos en un formato estructurado y transferirlos a otro responsable.', open: false },
  ];

  constructor(private router: Router) {}

  toggleRight(right: any) { right.open = !right.open; }

  goBack()    { this.router.navigate(['/habits']); }
  goToTerms() { this.router.navigate(['/terms']); }
}
