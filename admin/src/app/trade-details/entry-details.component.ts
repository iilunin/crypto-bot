import {AfterViewInit, Component, Input, OnInit, ViewChild} from '@angular/core';
import { MatExpansionPanel } from '@angular/material/expansion';
import {Mode, Entry, EntryTarget, TradeDetails} from '../trade-details';

@Component({
  selector: 'app-entry-details',
  templateUrl: './entry-details.component.html',
  styleUrls: ['./trade-details.component.css']
})

export class EntryDetailsComponent implements OnInit, AfterViewInit {
  @ViewChild(MatExpansionPanel) exp: MatExpansionPanel;
  
  @Input()
  trade: TradeDetails;

  @Input()
  mode: Mode;

  entryTarget: EntryTarget;

  constructor() {

  }
  
  ngOnInit(): void {
  }

  ngAfterViewInit(): void {
    // console.log(this.exp)
    // this.exp.expanded = true;
    this.exp.expanded = this.trade.entry? true : false;
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
      this.trade.entry = new Entry(null, !this.trade.isSell());
    }

    this.trade.entry.targets = [this.entryTarget];
  }
}

