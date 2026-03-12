import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { HabitsService } from '../../services/habits';
import { AuthenticationService } from '../../services/auth';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-habits',
  imports: [FormsModule, CommonModule],
  templateUrl: './habits.html',
  styleUrl: './habits.css'
})
export class Habits implements OnInit {
  habits: any[] = [];
  newHabitName = '';
  newHabitDescription = '';
  editingHabit: any = null;
  editName = '';
  editDescription = '';
  totalHabits = 0;
  todayCompleted = 0;
  completionRate = 0;
  weekCompletions = 0;
  today = new Date().toISOString().split('T')[0];

  constructor(
    private habitsService: HabitsService,
    private authService: AuthenticationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.habitsService.getHabits().subscribe(habits => {
      this.habits = habits;
      const stats = this.habitsService.getStats(habits);
      this.totalHabits = stats.totalHabits;
      this.todayCompleted = stats.todayCompleted;
      this.completionRate = stats.completionRate;
      this.weekCompletions = stats.weekCompletions;
    });
  }

  async addHabit() {
    if (!this.newHabitName.trim()) return;
    await this.habitsService.addHabit(this.newHabitName, this.newHabitDescription);
    this.newHabitName = '';
    this.newHabitDescription = '';
  }

  async completeHabit(habitId: string) {
    await this.habitsService.completeHabit(habitId);
  }

  isCompletedToday(habit: any): boolean {
    return habit.completed_dates?.includes(this.today) ?? false;
  }

  startEdit(habit: any) {
    this.editingHabit = habit;
    this.editName = habit.name;
    this.editDescription = habit.description || '';
  }

  cancelEdit() {
    this.editingHabit = null;
    this.editName = '';
    this.editDescription = '';
  }

  async saveEdit() {
    if (!this.editName.trim()) return;
    await this.habitsService.updateHabit(this.editingHabit.id, this.editName, this.editDescription);
    this.cancelEdit();
  }

  async deleteHabit(habitId: string) {
    if (confirm('¿Estás seguro de que quieres eliminar este hábito?')) {
      await this.habitsService.deleteHabit(habitId);
    }
  }

  getMotivationalMessage(): string {
    if (this.completionRate === 100) return '¡Perfecto! Completaste todos tus hábitos hoy. 🎉';
    if (this.completionRate >= 75) return '¡Excelente progreso! Casi lo logras. 💪';
    if (this.completionRate >= 50) return 'Vas por buen camino, ¡sigue así! 🚀';
    if (this.completionRate > 0) return '¡Buen comienzo, continúa con el momentum! ⚡';
    return '¡Comienza completando tu primer hábito hoy! 📝';
  }

  goToProfile() { this.router.navigate(['/profile']); }
  goToPrivacy() { this.router.navigate(['/privacy']); }
  goToTerms() { this.router.navigate(['/terms']); }
  goToContact() { this.router.navigate(['/contact']); }

  async logout() {
    await this.authService.logout();
    this.router.navigate(['/login']);
  }
}