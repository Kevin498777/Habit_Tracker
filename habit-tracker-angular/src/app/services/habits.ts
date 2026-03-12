import { Injectable } from '@angular/core';
import { Firestore, collection, addDoc,
         collectionData, deleteDoc, doc } from '@angular/fire/firestore';
import { Auth } from '@angular/fire/auth';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class HabitsService {

  constructor(private firestore: Firestore, private auth: Auth) {}

  // Obtener hábitos del usuario
  getHabits(): Observable<any[]> {
    const uid = this.auth.currentUser?.uid;
    const habitsRef = collection(this.firestore, `users/${uid}/habits`);
    return collectionData(habitsRef, { idField: 'id' });
  }

  // Agregar hábito
  addHabit(name: string, description: string = '') {
    const uid = this.auth.currentUser?.uid;
    const habitsRef = collection(this.firestore, `users/${uid}/habits`);
    return addDoc(habitsRef, { 
      name, 
      description,
      completed: false,
      createdAt: new Date() 
    });
  }

  // Eliminar hábito
  deleteHabit(habitId: string) {
    const uid = this.auth.currentUser?.uid;
    const habitDoc = doc(this.firestore, `users/${uid}/habits/${habitId}`);
    return deleteDoc(habitDoc);
  }
}
