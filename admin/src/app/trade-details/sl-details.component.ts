import {Component, Input, OnInit} from '@angular/core';
import {Mode, SLType, StopLoss, Target, TradeDetailMode, TradeDetails} from '../trade-details';


@Component({
  selector: 'app-sl-details',
  templateUrl: './sl-details.component.html',
  styleUrls: ['./trade-details.component.css']
})
export class SLDetailsComponent implements OnInit {
  private SLType = SLType;
  // private _trade: TradeDetails;

  @Input()
  trade: TradeDetails;

  @Input()
  mode: Mode;

  constructor() {

  }

  ngOnInit(): void {
  }

  addStopLoss() {
    if (!this.trade.stoploss) {
      this.trade.stoploss = new StopLoss();
    }
  }

  deleteStopLoss() {
    if (this.trade.stoploss) {
      this.trade.stoploss = null;
    }
  }

}
