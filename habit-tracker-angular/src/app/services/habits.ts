import { Injectable, inject } from '@angular/core';
import { Auth } from '@angular/fire/auth';
import { Firestore } from '@angular/fire/firestore';
import { Observable } from 'rxjs';
import { collection, addDoc, deleteDoc, doc,
         updateDoc, arrayUnion, query, onSnapshot } from '@angular/fire/firestore';

@Injectable({ providedIn: 'root' })
export class HabitsService {

  private auth = inject(Auth);
  private firestore = inject(Firestore);

  getHabits(): Observable<any[]> {
    return new Observable(observer => {
      const uid = this.auth.currentUser?.uid;
      if (!uid) {
        observer.next([]);
        return;
      }

      const habitsRef = collection(this.firestore, `users/${uid}/habits`);
      const q = query(habitsRef);

      const unsubscribe = onSnapshot(q, snapshot => {
        const habits = snapshot.docs.map(d => ({
          id: d.id,
          ...d.data()
        }));
        observer.next(habits);
      }, error => observer.error(error));

      return () => unsubscribe();
    });
  }

  addHabit(name: string, description: string = '') {
    const uid = this.auth.currentUser?.uid;
    const habitsRef = collection(this.firestore, `users/${uid}/habits`);
    return addDoc(habitsRef, {
      name,
      description,
      completed_dates: [],
      createdAt: new Date().toISOString()
    });
  }

  updateHabit(habitId: string, name: string, description: string = '') {
    const uid = this.auth.currentUser?.uid;
    const habitDoc = doc(this.firestore, `users/${uid}/habits/${habitId}`);
    return updateDoc(habitDoc, { name, description });
  }

  completeHabit(habitId: string) {
    const uid = this.auth.currentUser?.uid;
    const today = new Date().toISOString().split('T')[0];
    const habitDoc = doc(this.firestore, `users/${uid}/habits/${habitId}`);
    return updateDoc(habitDoc, { completed_dates: arrayUnion(today) });
  }

  deleteHabit(habitId: string) {
    const uid = this.auth.currentUser?.uid;
    const habitDoc = doc(this.firestore, `users/${uid}/habits/${habitId}`);
    return deleteDoc(habitDoc);
  }

  getStats(habits: any[]) {
    const today = new Date().toISOString().split('T')[0];
    const totalHabits = habits.length;
    const todayCompleted = habits.filter(h => h.completed_dates?.includes(today)).length;
    const completionRate = totalHabits > 0 ? Math.round((todayCompleted / totalHabits) * 100) : 0;

    const weekDates = Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - i);
      return d.toISOString().split('T')[0];
    });

    const weekCompletions = habits.filter(h =>
      h.completed_dates?.some((d: string) => weekDates.includes(d))
    ).length;

    return { totalHabits, todayCompleted, completionRate, weekCompletions };
  }

  getRecommendations(habits: any[]) {
    const names = habits.map(h => h.name.toLowerCase());
    const recs: any[] = [];

    if (!names.some(n => ['ejercicio','correr','gimnasio','deporte'].some(k => n.includes(k))))
      recs.push({ type: 'exercise', message: '¿Has considerado agregar ejercicio?', suggestion: 'Ejercicio diario — 30 min', priority: 'high' });

    if (!names.some(n => ['leer','lectura','libro'].some(k => n.includes(k))))
      recs.push({ type: 'reading', message: 'La lectura es un excelente hábito.', suggestion: 'Leer 20 minutos al día', priority: 'medium' });

    if (!names.some(n => ['meditar','meditación','mindfulness'].some(k => n.includes(k))))
      recs.push({ type: 'meditation', message: 'La meditación reduce el estrés.', suggestion: 'Meditar 10 minutos al día', priority: 'medium' });

    return recs;
  }
}