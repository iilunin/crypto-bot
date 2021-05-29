import {Component, OnDestroy, OnInit, TemplateRef, AfterViewInit, ViewChild} from '@angular/core';

import {TradeInfo} from '../tradeInfo';
import {BotApi} from '../botapi';
import {BinanceService} from '../binance.service';
import {Mode, TradeDetailMode} from '../trade-details';
import {AuthService} from '../auth.service';
import {Observable, Subscription, timer} from 'rxjs';
import {TradeService} from '../trade.service';
import {MatSort} from '@angular/material/sort';
import {MatTableDataSource} from '@angular/material/table';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { NotificationMessage, NotificationService, NotificatoinType } from '../services/notification.service';
import { TradeDetailsComponent } from '../trade-details/trade-details.component';
import { switchMap, tap } from 'rxjs/operators';

@Component({
  selector: 'app-asset-table',
  templateUrl: './asset-table.component.html',
  styleUrls: ['./asset-table.component.css']
})
export class AssetTableComponent implements OnInit, OnDestroy {
  private TradeDetailMode = TradeDetailMode;
  
  trades: TradeInfo[] = [];
  tradesDS: MatTableDataSource<TradeInfo> = null;
  ws_resubscribe: boolean = true;
  displayedColumns: string[] = ['ctrl-view-edit', 'sym', 'btc-val', 'price', 'balance', 'ctrl-pause', 'ctrl-close','ctrl-remove'];
  refreshInterval: number = 60000;
  symTrade: { [symbol: string ]: TradeInfo} = {};
  tradesDisabled: Set<string> = new Set<string>();
  private selectedTrade: TradeInfo;
  private isCloseTradeAction?: boolean;
  private symbolObserver?: any;
  // private loginSubscrition: Subscription;
  private tradeNotificationSubscription: Subscription;
  private timerSubscibtion: Subscription;
  @ViewChild(MatSort) sort: MatSort;

  constructor(
              private notificationService: NotificationService,
              private dialog: MatDialog,
              private api: BotApi,
              private binance: BinanceService,
              public auth: AuthService,
              private tradeService: TradeService) {
  }

  // ngAfterViewInit(): void {
  //   this.refreshTrades();
  // }

  ngOnInit() {
    this.timerSubscibtion = timer(0, this.refreshInterval).subscribe(tick => { this.refreshTrades(); })

    this.tradeNotificationSubscription = this.tradeService.eventAnounces$.subscribe(res => {
      if (res.type === 'created' || res.type === 'updated') {
        this.refreshTrades();
      }
    });
  }

  ngOnDestroy() {
    // this.loginSubscrition.unsubscribe();
    this.tradeNotificationSubscription.unsubscribe();
    this.timerSubscibtion.unsubscribe();
  }

  refreshTrades(): Subscription {
    return this.api.getActiveTrades().subscribe(
      trades => {
        trades.forEach(t => t.btcVal = t.price * (t.avail + t.locked));
        this.trades = trades;
        this.tradesDS = new MatTableDataSource(this.trades);
        this.tradesDS.sort = this.sort;
        this.ws_resubscribe = false;

        let newSymbols = this.trades.map(t => t.sym)
        let oldSymbols = Object.keys(this.symTrade)
        
        if (newSymbols.length != oldSymbols.length ||
          (newSymbols.sort().join() !== oldSymbols.sort().join())){
          this.ws_resubscribe = true;
        }
        
        if (this.ws_resubscribe){
          this.symTrade = {};
        }

        this.trades.forEach(t => this.symTrade[t.sym] = t);
        }
    , error => {
        this.trades = [];
        this.tradesDS = null;
        this.symTrade = {};

        if (this.symbolObserver) {
          this.symbolObserver.unsubscribe();
          this.symbolObserver = null;
        }

        this.showAlert(error, NotificatoinType.Alert);
    }, () => {
      if (this.trades.length > 0) {
        if (!this.ws_resubscribe){
          return;
        }
        console.log(`Subscribing websockets`)
        if (this.symbolObserver) {
          this.symbolObserver.unsubscribe();
        }

        this.symbolObserver = this.binance.listenSymbols(
          this.trades.map(t => t.sym.toLowerCase())).subscribe(
            res => this.onExchangeSymbolRcvd(res),
            err => console.log(err),
          () => console.log(`websocket completed`)
        );
      } else if (this.symbolObserver) {
        this.symbolObserver.unsubscribe();
        this.symbolObserver = null;
      }
    });
  }

  onExchangeSymbolRcvd(msg) {
    const tick = JSON.parse(msg);
    const ti = this.symTrade[tick.data.s];

    // TODO: should depend on buy or sell side

    // ti.currPriceA = tick.trade$.a;
    ti.price = tick.data.a;
    ti.btcVal = ti.price * (ti.avail + ti.locked);
    // ti.setCurrPrice(tick.trade$.b, tick.trade$.a);
    // ti.currPriceA = tick.trade$.a;
    // ti.currPriceB = tick.trade$.b;
    // // float(d['b']), 'a': float(d['a'])
    // console.log(ti);
  }

  onPauseAll() {
    this.api.pauseAllTrades().subscribe(result => {
      // this.tradesDisabled.delete(tradeInfo.id);
      if (result.status === 0) {
        this.trades.forEach(t => t.paused = true);
      }

      // this.validateAllTradesPaused();
    });
  }

  onResumeAll() {
    this.api.resumeAllTrades().subscribe(result => {
      // this.tradesDisabled.delete(tradeInfo.id);
      if (result.status === 0) {
        this.trades.forEach(t => t.paused = false);
      }
    });
  }

  onTradeInfo(tradeInfo: TradeInfo, mode: TradeDetailMode = TradeDetailMode.View) {
    TradeDetailsComponent.openDialog(this.dialog, new Mode(mode), tradeInfo?.id)
  }

  onPauseResume(tradeInfo: TradeInfo) {
    const shouldPause = !tradeInfo.paused;

    this.tradesDisabled.add(tradeInfo.id);

    this.api.pauseResumeTrade(tradeInfo.id, shouldPause).subscribe(result => {
      this.tradesDisabled.delete(tradeInfo.id);

      if (result.status === 0) {
        tradeInfo.paused = shouldPause;
        this.showAlert(`Trade ${tradeInfo.sym} was ${shouldPause ? 'paused' : 'resumed'}`);
      } else {
        this.showAlert(`Error ${shouldPause ? 'pausing' : 'resuming'} trade ${tradeInfo.sym}. ${result.msg}`, NotificatoinType.Warning);
      }

      // this.validateAllTradesPaused();
    });
  }

  // validateAllTradesPaused() {
  //   for (const trade of this.trades) {
  //     if (trade.paused) {
  //       this.allTradesPaused = true;
  //       return;
  //     }
  //   }
  //
  //   this.allTradesPaused = false;
  // }

  openModal(template: TemplateRef<any>, trade: TradeInfo, closeTrade: boolean) {
    this.selectedTrade = trade;
    this.isCloseTradeAction = closeTrade;
    const modalDialog = this.dialog.open(template);
    
    modalDialog.afterClosed().subscribe(() => {
      this.selectedTrade = null;
      this.isCloseTradeAction = null;
    });
  }

  confirm(): void {
    const isClose = this.isCloseTradeAction;

    if (this.isCloseTradeAction === true) {
      this.api.closeTrade(this.selectedTrade.id).subscribe(
        res => {
          this.handleCloseTradeRsp(res, isClose === true);
        }
      );
    } else if (this.isCloseTradeAction === false) {
      this.api.removeTrade(this.selectedTrade.id).subscribe(
        res => {
          this.handleCloseTradeRsp(res, isClose === true);
        }
      );
    }    
  }

  handleCloseTradeRsp(result, close) {
    if (result.status === 0) {
      this.refreshTrades();
      this.showAlert(`Trade successfully ${close ? 'closed' : 'removed'}`);
    } else {
      this.showAlert(`Trade ${close ? 'close' : 'remove'} failed. "${result.msg}"`, NotificatoinType.Alert);
    }
  }

  decline(): void {
  }

  showAlert(msg: string, type?: NotificatoinType) {
    this.notificationService.notification$.next(new NotificationMessage(msg, null, type))
  }
}
