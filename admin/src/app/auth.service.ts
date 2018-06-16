import {HttpClient, HttpHeaders} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {tap} from 'rxjs/operators';
import {moment} from 'ngx-bootstrap/chronos/test/chain';
import {Observable} from 'rxjs';

const httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json'
  })
};

@Injectable({ providedIn: 'root' })
export class AuthService {
  API_URL = 'http://127.0.0.1:3000/api/v1';

  constructor(private http: HttpClient) {

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
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('exp');
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
