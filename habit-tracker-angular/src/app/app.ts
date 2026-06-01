import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CookiesBanner } from './components/cookies-banner/cookies-banner';
import { Navbar } from './components/navbar/navbar';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, CookiesBanner, Navbar],
  templateUrl: './app.html',
})
export class App {}
