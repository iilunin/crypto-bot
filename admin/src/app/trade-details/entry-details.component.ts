import {Component, Input, OnInit} from '@angular/core';
import {Mode, Entry, EntryTarget, TradeDetails} from '../trade-details';

@Component({
  selector: 'app-entry-details',
  templateUrl: './entry-details.component.html',
  styleUrls: ['./trade-details.component.css']
})

export class EntryDetailsComponent implements OnInit {
  @Input()
  trade: TradeDetails;

  @Input()
  mode: Mode;

  entryTarget: EntryTarget;

  constructor() {

  }

  ngOnInit(): void {
  }

  deleteTarget(exitTarget: EntryTarget) {
    this.entryTarget = null;
    this.trade.entry = null;
  }

  addNewTarget() {
    if (this.entryTarget) {
      return;
    }

    this.entryTarget = new EntryTarget();

    if (!this.trade.entry) {
      this.trade.entry = new Entry(!this.trade.isSell());
    }

    this.trade.entry.targets = [this.entryTarget];
  }
}

