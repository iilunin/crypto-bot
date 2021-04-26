import {AfterViewInit, Component, ElementRef, Input, OnInit, ViewChild} from '@angular/core';
import { MatExpansionPanel } from '@angular/material/expansion';
import {Mode, SLType, StopLoss, TradeDetails} from '../trade-details';


@Component({
  selector: 'app-sl-details',
  templateUrl: './sl-details.component.html',
  styleUrls: ['./trade-details.component.css']
})
export class SLDetailsComponent implements OnInit, AfterViewInit {
  private SLType = SLType;
  // private _trade: TradeDetails;

  @ViewChild(MatExpansionPanel) exp: MatExpansionPanel;
  @Input()
  trade: TradeDetails;

  @Input()
  mode: Mode;

  constructor() {

  }

  ngOnInit(): void {
    
  }

  ngAfterViewInit(): void {
    this.exp.expanded = this.trade.stoploss? true:false;
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
