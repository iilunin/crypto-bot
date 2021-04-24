import { Injectable } from '@angular/core';
import {HttpClient, HttpErrorResponse, HttpHeaders} from '@angular/common/http';
import {Observable, of, throwError} from 'rxjs';
import {TradeInfo} from './tradeInfo';
import {catchError, map, retry, tap} from 'rxjs/operators';
import {ApiResult} from './apiresult';
import {TradeDetails, Entry} from './trade-details';
import deleteProperty = Reflect.deleteProperty;
import {environment} from '../environments/environment';
import { Balance } from './balance';


const httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json'
  })
};

export class BinancePriceResult {
  symbol: string;
  bestAsk: string;
  bestBid: string;
}

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

  bookTicker(symbol: string): Observable<BinancePriceResult> {
    return this.http.get<any>(`${this.API_URL}/orderbook/${symbol}`, httpOptions).pipe(
      retry(this.RETRIES),
      map(data => {
        if (!data)
          return null;
          
        const result = new BinancePriceResult();
        result.symbol = data.symbol;
        result.bestAsk = data.askPrice;
        result.bestBid = data.bidPrice;
        return result;
      }),
      catchError(this.handleError('getActiveTradeInfo', null))
    );
  }


  getActiveTradeInfo(id: string): Observable<TradeDetails> {
    return this.http.get<TradeDetails>(`${this.API_URL}/trade/${id}`, httpOptions).pipe(
      retry(this.RETRIES),
      tap(trade => this.log(`fetched trade ${id} info`)),
      map(data => {
        const trade = new TradeDetails(false, data);
        // if (data.entry) {
        //   trade.entry = new Entry(data.entry); // restore nested class Entry
        // }
        return trade;
      }),
      catchError(this.handleError('getActiveTradeInfo', null))
    );
  }

  getActiveTrades(): Observable<TradeInfo[]> {
    return this.http.get<TradeInfo[]>(`${this.API_URL}/trades`).pipe(
      retry(this.RETRIES),
      map(trades => trades.map(trade => new TradeInfo(trade))),
      tap(trades => this.log(`fetched trades`)),
      catchError(this.handleError('getActiveTrades', [])));
  }

  getExchangeInfo(): Observable<any> {
    return this.http.get<any>(`${this.API_URL}/info`).pipe(
      retry(this.RETRIES),
      catchError(this.handleError('getExchangeInfo', []))
    );
  }

  getBalances(force=false): Observable<Balance[]> {
    return this.http.get<any>(`${this.API_URL}/balance/${force?'1':'0'}`, httpOptions).pipe(
      retry(this.RETRIES),
      map(data => {
        const balanceList: Balance[] = [];
        
        for (let key in data) {
          balanceList.push(new Balance({sym: key, avail: data[key].f, locked: data[key].l}))
        }

        return balanceList;
      }),
      // tap(trades => this.log(`fetched trades`)),
      catchError(this.handleError('getBalances', []))
    );
  }

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


