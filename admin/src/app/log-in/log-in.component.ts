import { Component, OnInit } from '@angular/core';
import {AuthService} from '../auth.service';
import {NgForm} from '@angular/forms';

@Component({
  selector: 'app-log-in',
  templateUrl: './log-in.component.html',
  styleUrls: ['./log-in.component.css']
})
export class LogInComponent implements OnInit {
  private login: string;
  private password: string;
  private error: string;

  constructor(public auth: AuthService) { }

  ngOnInit() {
  }

  onSubmit(evt) {
    this.auth.login(this.login, this.password).subscribe(
      (res) => {
        this.login = '';
        this.password = '';
        this.error = '';
      },
      (e) => {
        if (e.error && e.error.msg) {
          this.error = e.error.msg;
        }
      }
      // res =>  { if (res.jwt) {
      //   this.refreshTrades();
      // }}
    );
  }
}
