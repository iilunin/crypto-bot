import {HttpClient, HttpHeaders} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {tap} from 'rxjs/operators';
import * as  moment from 'moment';
import {Observable, Subject} from 'rxjs';
import {environment} from '../environments/environment';

const httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json'
  })
};

@Injectable({ providedIn: 'root' })
export class AuthService {
  API_URL = `${environment.BOT_API_URL}/api/v1`;

  private loginAnouceSource = new Subject<boolean>();
  loginEventAnounced$ =  this.loginAnouceSource.asObservable();

  constructor(private http: HttpClient) {
    console.log(this.API_URL);
  }

  login(user: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.API_URL}/auth`, {'username': user, 'password': password}, httpOptions).pipe(
      tap(authResult => this.setSession(authResult))
    );
  }

  private setSession(authResult) {
    const expiresAt = moment().add(authResult.exp, 'second');

    localStorage.setItem('token', authResult.jwt);
    localStorage.setItem('exp', JSON.stringify(expiresAt.valueOf()) );
    this.loginAnouceSource.next(true);
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('exp');
    this.loginAnouceSource.next(false);
  }

  public isLoggedIn() {
    return moment().isBefore(this.getExpiration());
  }

  isLoggedOut() {
    return !this.isLoggedIn();
  }

  getExpiration() {
    const expiration = localStorage.getItem('exp');
    const expiresAt = JSON.parse(expiration);
    return moment(expiresAt);
  }
}
