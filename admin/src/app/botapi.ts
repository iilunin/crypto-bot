import { Injectable } from '@angular/core';
import {HttpClient, HttpErrorResponse, HttpHeaders} from '@angular/common/http';
import {Observable, of, throwError} from 'rxjs';
import {TradeInfo} from './tradeInfo';
import {catchError, map, retry, tap} from 'rxjs/operators';
import {ApiResult} from './apiresult';
import {TradeDetails, Entry} from './trade-details';
import deleteProperty = Reflect.deleteProperty;
import {environment} from '../environments/environment';


const httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json'
  })
};

@Injectable({ providedIn: 'root' })
export class BotApi {
  RETRIES = 2;
  API_URL = `${environment.BOT_API_URL}/api/v1`;

  constructor(private http: HttpClient) {
  }

  addTrade(trade: TradeDetails ): Observable<ApiResult> {
    const sanitizedTrade: any = Object.assign({}, trade, {stoploss: trade.stoploss});
    deleteProperty(sanitizedTrade, '_stoploss');

    // console.log(o);
    return this.http.post<ApiResult>(`${this.API_URL}/trade/0`,
                                          JSON.stringify({action: 'add', data: {trade: sanitizedTrade} }),
                                          httpOptions).pipe(
      // tap(_ => this.log(`Trade ${id} is closed`)),
      catchError(this.handleError('closeTrade'))
    );
  }

  getActiveTradeInfo(id: string): Observable<TradeDetails> {
    return this.http.get<TradeDetails>(`${this.API_URL}/trade/${id}`, httpOptions).pipe(
      retry(this.RETRIES),
      tap(trade => this.log(`fetched trade ${id} info`)),
      map(data => {
        const trade = Object.assign(new TradeDetails(), data);
        if (data.entry) {
          trade.entry = Object.assign(new Entry(), data.entry); // restore nested class Entry
        }
        return trade;
      }),
      catchError(this.handleError('getActiveTradeInfo', null))
    );
  }

  getActiveTrades(): Observable<TradeInfo[]> {
    return this.http.get<TradeInfo[]>(`${this.API_URL}/trades`).pipe(
      retry(this.RETRIES),
      tap(trades => this.log(`fetched trades`)),
      catchError(this.handleError('getActiveTrades', []))
    );
  }

  getExchangeInfo(): Observable<any> {
    return this.http.get<any>(`${this.API_URL}/info`).pipe(
      retry(this.RETRIES),
      // tap(trades => this.log(`fetched trades`)),
      catchError(this.handleError('getExchangeInfo', []))
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

  removeTrade(id: string ): Observable<ApiResult> {
    if (id === undefined || id === null) {
      id = '0';
    }

    return this.http.delete<ApiResult>(`${this.API_URL}/trade/${id}`, httpOptions).pipe(
      tap(_ => this.log(`Trade ${id} is removed`)),
      catchError(this.handleError('removeTrade'))
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
  private handleError<T> (operation, result?: T) {
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


