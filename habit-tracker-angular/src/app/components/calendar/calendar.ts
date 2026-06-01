import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HabitsService } from '../../services/habits';

interface CalendarDay {
  day: number;
  date: string;
  empty: boolean;
  isToday: boolean;
  completionLevel: 'none' | 'single' | 'partial' | 'full';
  completedCount: number;
  totalCount: number;
  tooltip: string;
  habitsCompleted: string[];
}

@Component({
  selector: 'app-calendar',
  imports: [CommonModule, FormsModule],
  templateUrl: './calendar.html',
  styleUrl: './calendar.css'
})
export class Calendar implements OnInit {
  habits: any[] = [];
  selectedHabitId = '';

  currentYear: number;
  currentMonth: number;  // 1-based
  today: string;

  calendarDays: CalendarDay[] = [];
  monthName = '';

  monthStats = { totalCompletions: 0, activeDays: 0, bestStreak: 0 };

  private monthNames = [
    'Enero','Febrero','Marzo','Abril','Mayo','Junio',
    'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'
  ];

  constructor(private habitsService: HabitsService, private router: Router) {
    const now = new Date();
    this.currentYear = now.getFullYear();
    this.currentMonth = now.getMonth() + 1;
    this.today = now.toISOString().split('T')[0];
  }

  ngOnInit() {
    this.habitsService.getHabits().subscribe(habits => {
      this.habits = habits;
      this.buildCalendar();
    });
  }

  get prevYear()  { return this.currentMonth === 1  ? this.currentYear - 1 : this.currentYear; }
  get prevMonth() { return this.currentMonth === 1  ? 12 : this.currentMonth - 1; }
  get nextYear()  { return this.currentMonth === 12 ? this.currentYear + 1 : this.currentYear; }
  get nextMonth() { return this.currentMonth === 12 ? 1  : this.currentMonth + 1; }

  navigatePrev() {
    this.currentYear  = this.prevYear;
    this.currentMonth = this.prevMonth;
    this.buildCalendar();
  }

  navigateNext() {
    this.currentYear  = this.nextYear;
    this.currentMonth = this.nextMonth;
    this.buildCalendar();
  }

  onHabitFilterChange() { this.buildCalendar(); }
  clearFilter() { this.selectedHabitId = ''; this.buildCalendar(); }

  buildCalendar() {
    this.monthName = this.monthNames[this.currentMonth - 1];

    const filteredHabits = this.selectedHabitId
      ? this.habits.filter(h => h.id === this.selectedHabitId)
      : this.habits;

    const totalHabits = filteredHabits.length;
    const firstDay = new Date(this.currentYear, this.currentMonth - 1, 1);
    const lastDay  = new Date(this.currentYear, this.currentMonth, 0);

    // Monday-based week: Monday=0 ... Sunday=6
    let startOffset = firstDay.getDay() - 1;
    if (startOffset < 0) startOffset = 6;

    this.calendarDays = [];

    // Empty cells before month start
    for (let i = 0; i < startOffset; i++) {
      this.calendarDays.push({ day: 0, date: '', empty: true, isToday: false,
        completionLevel: 'none', completedCount: 0, totalCount: 0, tooltip: '', habitsCompleted: [] });
    }

    const completionsByDate: Record<string, string[]> = {};
    for (const habit of filteredHabits) {
      const dates: string[] = habit.completed_dates || [];
      for (const d of dates) {
        if (!completionsByDate[d]) completionsByDate[d] = [];
        completionsByDate[d].push(habit.name);
      }
    }

    let totalCompletions = 0;
    const activeDays: string[] = [];

    for (let d = 1; d <= lastDay.getDate(); d++) {
      const mm = String(this.currentMonth).padStart(2, '0');
      const dd = String(d).padStart(2, '0');
      const dateStr = `${this.currentYear}-${mm}-${dd}`;

      const completed = completionsByDate[dateStr] || [];
      const completedCount = this.selectedHabitId ? (completed.length > 0 ? 1 : 0) : completed.length;

      let completionLevel: CalendarDay['completionLevel'] = 'none';
      if (totalHabits > 0 && completedCount > 0) {
        if (this.selectedHabitId) {
          completionLevel = completedCount > 0 ? 'full' : 'none';
        } else {
          const ratio = completedCount / totalHabits;
          if (ratio >= 1)    completionLevel = 'full';
          else if (ratio >= 0.5) completionLevel = 'partial';
          else               completionLevel = 'single';
        }
      }

      if (completedCount > 0) {
        totalCompletions += completedCount;
        activeDays.push(dateStr);
      }

      const tooltip = completed.length > 0 ? completed.join(', ') : '';

      this.calendarDays.push({
        day: d, date: dateStr, empty: false,
        isToday: dateStr === this.today,
        completionLevel, completedCount,
        totalCount: totalHabits,
        tooltip, habitsCompleted: completed
      });
    }

    this.monthStats = {
      totalCompletions,
      activeDays: activeDays.length,
      bestStreak: this.calcBestStreak(activeDays)
    };
  }

  private calcBestStreak(activeDays: string[]): number {
    if (!activeDays.length) return 0;
    const sorted = [...activeDays].sort();
    let best = 1, current = 1;
    for (let i = 1; i < sorted.length; i++) {
      const prev = new Date(sorted[i - 1]);
      const curr = new Date(sorted[i]);
      const diff = (curr.getTime() - prev.getTime()) / 86400000;
      if (diff === 1) { current++; best = Math.max(best, current); }
      else current = 1;
    }
    return best;
  }

  getSelectedHabitName(): string {
    const h = this.habits.find(x => x.id === this.selectedHabitId);
    return h?.name || '';
  }

  goToHabits() { this.router.navigate(['/habits']); }
}
