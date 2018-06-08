import {Component, Input, OnInit} from '@angular/core';
import {Mode, Target, TradeDetails} from '../trade-details';

@Component({
  selector: 'app-exit-details',
  templateUrl: './exit-details.component.html',
  styleUrls: ['./trade-details.component.css']
})

export class ExitDetailsComponent implements OnInit {
  @Input()
  trade: TradeDetails;

  @Input()
  mode: Mode

  lastAddedTarget: Target;

  constructor() {

  }

  ngOnInit(): void {
    // console.log(this.trade.exit.targets[0]);
  }

  deleteTarget(exitTarget: Target) {
    this.trade.exit.targets = this.trade.exit.targets.filter(et => et !== exitTarget);
  }

  addNewTarget() {
    if (this.lastAddedTarget && !this.lastAddedTarget.price)
      return;
    this.lastAddedTarget = new Target();
    this.trade.exit.targets.push(this.lastAddedTarget);
  }
}
