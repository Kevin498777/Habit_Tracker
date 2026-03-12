import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CookiesBanner } from './components/cookies-banner/cookies-banner';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, CookiesBanner],
  templateUrl: './app.html',
})
export class App {}