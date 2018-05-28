import { Component, OnInit, TemplateRef } from '@angular/core';
import { BsModalService } from 'ngx-bootstrap/modal';
import { BsModalRef } from 'ngx-bootstrap/modal/bs-modal-ref.service';

import {TradeInfo} from '../tradeInfo';
import {BotApi} from '../botapi';
import {AlertComponent} from 'ngx-bootstrap';

@Component({
  selector: 'app-asset-table',
  templateUrl: './asset-table.component.html',
  styleUrls: ['./asset-table.component.css']
})
export class AssetTableComponent implements OnInit {
  // allTradesPaused: boolean
  trades: TradeInfo[] = [];
  tradesDisabled: Set<string> = new Set<string>();
  alerts: any[] = [];
  private modalRef: BsModalRef;
  private closeTradeId: string;
  private closeTrade?: boolean;

  constructor(private modalService: BsModalService, private api: BotApi) {}

  ngOnInit() {
    // this.validateAllTradesPaused();
    this.getTrades();
  }


  getTrades() {
    this.api.getActiveTrades().subscribe(trades => this.trades = trades, error => {
      this.alerts.push({
        type: 'danger',
        msg: error,
        timeout: 5000
      });
    });
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

  onPauseResume(tradeInfo: TradeInfo) {
    const shouldPause = !tradeInfo.paused;

    this.tradesDisabled.add(tradeInfo.id);

    this.api.pauseResumeTrade(tradeInfo.id, shouldPause).subscribe(result => {
      this.tradesDisabled.delete(tradeInfo.id);

      if (result.status === 0) {
        tradeInfo.paused = shouldPause;
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
    this.closeTradeId = tradeId;
    this.closeTrade = closeTrade;
    this.modalRef = this.modalService.show(template, {class: 'modal-md'});
  }

  confirm(): void {
    if (this.closeTrade === true) {
      this.api.closeTrade(this.closeTradeId).subscribe(this.handleCloseTradeRsp.bind(this));
    } else if (this.closeTrade === false) {
      console.log('remove trade');
    }
    this.closeTradeId = null;
    this.closeTrade = null;
    this.modalRef.hide();
  }

  handleCloseTradeRsp(result) {
    if (result.status === 0) {
      this.getTrades();
    }
  }

  decline(): void {
    this.closeTradeId = null;
    this.closeTrade = null;
    this.modalRef.hide();
  }

  onClosedAlert(dismissedAlert: AlertComponent): void {
    this.alerts = this.alerts.filter(alert => alert !== dismissedAlert);
  }
}
