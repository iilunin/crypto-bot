import {Component, OnDestroy, OnInit, TemplateRef} from '@angular/core';
import { BsModalService } from 'ngx-bootstrap/modal';
import { BsModalRef } from 'ngx-bootstrap/modal/bs-modal-ref.service';

import {TradeInfo} from '../tradeInfo';
import {BotApi} from '../botapi';
import {AlertComponent} from 'ngx-bootstrap';
import {BinanceService} from '../binance.service';
import {Router, RouterModule} from '@angular/router';
import {TradeDetailMode} from '../trade-details';
import {AuthService} from '../auth.service';
import {Subscription} from 'rxjs';
import {TradeService} from '../trade.service';

@Component({
  selector: 'app-asset-table',
  templateUrl: './asset-table.component.html',
  styleUrls: ['./asset-table.component.css']
})
export class AssetTableComponent implements OnInit, OnDestroy {
  private TradeDetailMode = TradeDetailMode;
  trades: TradeInfo[] = [];
  symTrade: { [symbol: string ]: TradeInfo} = {};
  tradesDisabled: Set<string> = new Set<string>();
  alerts: any[] = [];
  private modalRef: BsModalRef;
  private selectedTradeId: string;
  private isCloseTradeAction?: boolean;
  private symbolObserver?: any;
  private loginSubscrition: Subscription;
  private tradeNotificationSubscription: Subscription;

  constructor(private modalService: BsModalService,
              private api: BotApi,
              private binance: BinanceService,
              private router: Router,
              public auth: AuthService,
              private tradeService: TradeService) {


  }

  ngOnInit() {
    this.loginSubscrition = this.auth.loginEventAnounced$.subscribe(res => {
        if (res === true) {
          this.refreshTrades();
        }
      }
    );
    // this.validateAllTradesPaused();
    // this.refreshTrades();
    // this.checkAuth();
    if (this.auth.isLoggedIn()) {
      this.refreshTrades();
    }

    this.tradeNotificationSubscription = this.tradeService.eventAnounces$.subscribe(res => {
      console.log(res);
      if (res.type === 'created') {
        this.refreshTrades();
        // setTimeout(this.refreshTrades.bind(this), 0);
      }
    });
  }

  ngOnDestroy() {
    this.loginSubscrition.unsubscribe();
    this.tradeNotificationSubscription.unsubscribe();
  }

  // checkAuth() {
  //   if (!this.auth.isLoggedIn()) {
  //     this.auth.login('test', 'test').subscribe(
  //       res =>  { if (res.jwt) {
  //         this.refreshTrades();
  //       }}
  //     );
  //   } else {
  //     this.refreshTrades();
  //   }
  // }

    refreshTrades() {
    this.api.getActiveTrades().subscribe(
      trades => {
        trades.forEach(t => t.btcVal = t.price * (t.avail + t.locked));
        this.trades = trades;
        this.symTrade = {};
        this.trades.forEach(t => this.symTrade[t.sym] = t);
        }
    , error => {
        this.trades = [];
        this.symTrade = {};

        if (this.symbolObserver) {
          this.symbolObserver.unsubscribe();
          this.symbolObserver = null;
        }

        this.alerts.push({
          type: 'danger',
          msg: error,
          timeout: 5000
        });
    }, () => {
      if (this.trades.length > 0) {
        if (this.symbolObserver) {
          this.symbolObserver.unsubscribe();
        }
        // this.binance.getOrderBookTickers().subscribe(orderbook => console.log(orderbook));
        this.symbolObserver = this.binance.listenSymbols(
          this.trades.map(t => t.sym.toLowerCase())).subscribe(
            this.onExchangeSymbolRcvd.bind(this),
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

    this.router.navigate(['/trades',
        { outlets: { trade: [tradeInfo ? tradeInfo.id : '0', {mode: mode} ]} }
      ]);
    // this.router.navigate([
    //       { outlets: { tradeDetails: ['trades', tradeInfo.id, {edit: edit} ]} }
    //   ]);
    // this.router.navigate(['trades', tradeInfo.id, {edit: edit} ]);
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
        this.showAlert(`Error ${shouldPause ? 'pausing' : 'resuming'} trade ${tradeInfo.sym}. ${result.msg}`, 'danger');
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

  openModal(template: TemplateRef<any>, tradeId: string, closeTrade: boolean) {
    this.selectedTradeId = tradeId;
    this.isCloseTradeAction = closeTrade;
    this.modalRef = this.modalService.show(template, {class: 'modal-md'});
  }

  confirm(): void {
    const isClose = this.isCloseTradeAction;

    if (this.isCloseTradeAction === true) {
      this.api.closeTrade(this.selectedTradeId).subscribe(
        res => {
          this.handleCloseTradeRsp(res, isClose === true);
        }
      );
    } else if (this.isCloseTradeAction === false) {
      this.api.removeTrade(this.selectedTradeId).subscribe(
        res => {
          this.handleCloseTradeRsp(res, isClose === true);
        }
      );
      console.log('Remove trade');
    }
    this.selectedTradeId = null;
    this.isCloseTradeAction = null;
    this.modalRef.hide();
  }

  handleCloseTradeRsp(result, close) {
    if (result.status === 0) {
      this.refreshTrades();
      this.showAlert(`Trade successfully ${close ? 'closed' : 'removed'}`);
    } else {
      this.showAlert(`Trade ${close ? 'close' : 'remove'} failed. "${result.msg}"`, 'danger');
    }
  }

  decline(): void {
    this.selectedTradeId = null;
    this.isCloseTradeAction = null;
    this.modalRef.hide();
  }

  onClosedAlert(dismissedAlert: AlertComponent): void {
    this.alerts = this.alerts.filter(alert => alert !== dismissedAlert);
  }

  showAlert(msg: string, type = 'success', timeout = 3000) {
    this.alerts.push({
      type: type,
      msg: msg,
      timeout: timeout
    });
  }
}
