import { Injectable } from '@angular/core';
import {HttpClient, HttpErrorResponse, HttpHeaders} from '@angular/common/http';
import {Observable, of, throwError} from 'rxjs';
import {TradeInfo} from './tradeInfo';
import {catchError, map, retry, tap} from 'rxjs/operators';
import {ApiResult} from './apiresult';


const httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json'
  })
};

@Injectable({ providedIn: 'root' })
export class BotApi {
  API_URL = 'http://127.0.0.1:3000/api/v1';

  constructor(private http: HttpClient) { }

  getActiveTrades(): Observable<TradeInfo[]> {
    return this.http.get<TradeInfo[]>(`${this.API_URL}/trades`).pipe(
      retry(3),
      tap(trades => this.log(`fetched trades`)),
      catchError(this.handleError('getActiveTrades', []))
    );
  }

  // private handleError<T>(error: HttpErrorResponse, def: T[]): Observable<T[]> {
  //   if (error.error instanceof ErrorEvent) {
  //     // A client-side or network error occurred. Handle it accordingly.
  //     console.error('An error occurred:', error.error.message);
  //   } else {
  //     // The backend returned an unsuccessful response code.
  //     // The response body may contain clues as to what went wrong,
  //     console.error(
  //       `Backend returned code ${error.status}, ` +
  //       `body was: ${error.error}`);
  //   }
  //   // return an observable with a user-facing error message
  //   return throwError(
  //     'Something bad happened; please try again later.');
  // }

  // pauseTrade(id: string ): Observable<ApiResult> {
  //   return this.pauseResumeTrade(id, true);
  // }
  //
  // resumeTrade(id: string ): Observable<ApiResult> {
  //   return this.pauseResumeTrade(id, false);
  // }

  pauseAllTrades(): Observable<ApiResult> {
   return this.pauseResumeTrade('0', true);
  }

  resumeAllTrades(): Observable<ApiResult> {
    return this.pauseResumeTrade('0', false);
  }

  pauseResumeTrade(id: string, pause: boolean ): Observable<ApiResult> {
    const pauseOrResume = pause ? 'pause' : 'resume';

    return this.http.post<ApiResult>(`${this.API_URL}/trade/${id}`, JSON.stringify({action: pauseOrResume}), httpOptions).pipe(
      tap(_ => this.log(`All treades are ` + pause ? 'paused' : 'resumed')),
      catchError(this.handleError('pauseResumeTrade'))
    );
  }

  closeTrade(id: string ): Observable<ApiResult> {

    if (id === undefined || id === null) {
      id = '0';
    }

    return this.http.post<ApiResult>(`${this.API_URL}/trade/${id}`, JSON.stringify({action: 'close'}), httpOptions).pipe(
      tap(_ => this.log(`Trade ${id} is closed`)),
      catchError(this.handleError('closeTrade'))
    );
  }

  private log(message: string) {
    console.log('BotApi: ' + message);
  }

  /**
   * Handle Http operation that failed.
   * Let the app continue.
   * @param operation - name of the operation that failed
   * @param result - optional value to return as the observable result
   */
  private handleError<T> (operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {

      // TODO: send the error to remote logging infrastructure
      console.error(error); // log to console instead

      // TODO: better job of transforming error for user consumption
      this.log(`${operation} failed: ${error.message}`);

      if (error.status === 0) {
        return throwError('No connectivity to the bot');
      }
      // Let the app keep running by returning an empty result.
      return of(result as T);
    };
  }
}


