import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthenticationService } from '../../services/auth';
import { HabitsService } from '../../services/habits';

@Component({
  selector: 'app-profile',
  imports: [CommonModule],
  templateUrl: './profile.html',
  styleUrl: './profile.css'
})
export class Profile implements OnInit {
  user: any = null;
  habitCount = 0;
  completedToday = 0;
  weekCompletions = 0;
  completionRate = 0;
  recommendations: any[] = [];

  today = new Date().toISOString().split('T')[0];

  constructor(
    private authService: AuthenticationService,
    private habitsService: HabitsService,
    private router: Router
  ) {}

  ngOnInit() {
    this.user = this.authService.getCurrentUser();

    this.habitsService.getHabits().subscribe(habits => {
      const stats = this.habitsService.getStats(habits);
      this.habitCount = stats.totalHabits;
      this.completedToday = stats.todayCompleted;
      this.weekCompletions = stats.weekCompletions;
      this.completionRate = stats.completionRate;
      this.recommendations = this.habitsService.getRecommendations(habits);
    });
  }

  getInitial(): string {
    return this.user?.displayName?.charAt(0)?.toUpperCase()
      || this.user?.email?.charAt(0)?.toUpperCase()
      || '?';
  }

  goToHabits() {
    this.router.navigate(['/habits']);
  }

  async logout() {
    await this.authService.logout();
    this.router.navigate(['/login']);
  }
}