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

  constructor(
    private habitsService: HabitsService,
    private authService: AuthenticationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.habitsService.getHabits().subscribe(habits => {
      this.habits = habits;
    });
  }

  async addHabit() {
    if (!this.newHabitName.trim()) return;
    await this.habitsService.addHabit(this.newHabitName, this.newHabitDescription);
    this.newHabitName = '';
    this.newHabitDescription = '';
  }

  async deleteHabit(habitId: string) {
    await this.habitsService.deleteHabit(habitId);
  }

  async logout() {
    await this.authService.logout();
    this.router.navigate(['/login']);
  }
}