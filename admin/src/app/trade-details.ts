import {st} from '@angular/core/src/render3';

export enum TradeStatus {
  NEW = 'NEW',
  ACTIVE = 'ACTIVE',
  COMPLETED = 'COMPLETED'
}

export enum SLType {
  FIXED = 'FIXED',
  TRAILING = 'TRAILING'
}

export class Target {
  status: TradeStatus;
  id: number;
  date: string;
  price: string;
  vol: string;
  smart: boolean;
  sl: string;
  best_price: string;
  isCompleted(): boolean { return this.status === TradeStatus.COMPLETED; }
}

export class ExitInfo {
  constructor() {
    this.targets = [];
    this.threshold = 0.4.toLocaleString() + '%';
  }
  smart: boolean;
  threshold: string;
  targets: Target[];
}

export class StopLoss {
  type: SLType = SLType.FIXED;
  threshold = '5%';
  initial_target: Target;

  constructor() {
    this.initial_target = new Target();
    this.initial_target.vol = '100%';
  }
  isFixed(): boolean { return this.type === SLType.FIXED; }
  isTrailing(): boolean { return this.type === SLType.TRAILING; }
}

export class TradeDetails {

  private _stoploss: StopLoss;

  id: string;
  asset: string;
  cap: string;
  symbol = '';
  side: 'BUY' | 'SELL' = 'SELL';
  status: 'NEW' | 'ACTIVE' | 'COMPLETED';
  exit: ExitInfo;
  entry?: Entry;

  get stoploss(): StopLoss {
    return this._stoploss;
  }

  set stoploss(stoploss: StopLoss) {
    if (!stoploss) {
      this._stoploss = null;
    } else if (stoploss instanceof StopLoss) {
      this._stoploss = stoploss;
    } else {
      this._stoploss = Object.assign(new StopLoss(), stoploss);
    }
  }

  constructor(create_new: boolean = false) {
    if (create_new) {
      this.exit = new ExitInfo();
      this.id = this.generateGuid();
    }
  }

  // getInstance<T>(obj: T, c: new () => T): T {
  //   if (!obj) {
  //     return null;
  //   } else if (obj instanceof T) {
  //     return obj;
  //   } else {
  //     Object.assign(c(), obj);
  //   }
  // }

  isBuy(): boolean { return this.side === 'BUY'; }
  isSell(): boolean { return !this.isBuy(); }

  generateGuid(): string {
    let result = '';
    let i: string;
    let j: number;

    for (j = 0; j < 32; j++) {
      if (j === 8 || j === 12 || j === 16 || j === 20) {
        result = result + '-';
      }
      i = Math.floor(Math.random() * 16).toString(16).toUpperCase();
      result = result + i;
    }

    return result;
  }
}

export class EntryTarget {
  price: string;
  vol: string;
}

export class Entry {
  constructor(sell: boolean = true) {
    this.targets = [new EntryTarget()];
    this.setIsSell(sell);
  }

  side: 'BUY' | 'SELL' = 'BUY';
  targets: [EntryTarget];
  smart: boolean;

  isBuy(): boolean { return this.side === 'BUY'; }
  isSell(): boolean { return !this.isBuy(); }
  setIsSell(sell: boolean): void {
    if (sell) { this.side = 'SELL'; } else { this.side = 'BUY'; }
  }
}



export enum TradeDetailMode {
  View = 'view',
  Edit = 'edit',
  Create = 'new'
}

export class Mode {
  constructor(private mode: TradeDetailMode) {}

  isView(): boolean { return this.mode === TradeDetailMode.View; }
  isEdit(): boolean { return this.mode === TradeDetailMode.Edit; }
  isCreate(): boolean { return this.mode === TradeDetailMode.Create; }

  setEdit(): void { this.mode = TradeDetailMode.Edit; }
  setView(): void { this.mode = TradeDetailMode.View; }

  str(): string {
    if (this.mode === TradeDetailMode.View) { return 'View'; }
    if (this.mode === TradeDetailMode.Edit) { return 'Edit'; }
    if (this.mode === TradeDetailMode.Create) { return 'Create'; }

    return 'Unknown';
  }

}
