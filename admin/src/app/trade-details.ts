export class TradeDetails {
  constructor(create_new: boolean = false) {
    if (create_new) {
      this.exit = new ExitInfo();
      this.id = this.generateGuid();
    }
  }

  id: string;
  asset: string;
  symbol: string = '';
  side: 'BUY' | 'SELL';
  isBuy(): boolean { return this.side === 'BUY'; }
  isSell(): boolean { return !this.isBuy(); }
  status: 'NEW' | 'ACTIVE' | 'COMPLETED';
  exit: ExitInfo;
  stoploss: StopLoss;

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

export class ExitInfo {
  constructor() {
    this.targets = [];
    this.threshold = 0.4.toLocaleString() + '%';
  }
  smart: boolean;
  threshold: string;
  targets: Target[];

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
}

export class StopLoss {
  type: SLType = SLType.FIXED;
  threshold: string = '5%';
  initial_target: Target;
}

export enum SLType {
  FIXED = 'FIXED',
  TRAILING = 'TRAILING'
}

export enum TradeStatus {
  NEW = 'NEW',
  ACTIVE = 'ACTIVE',
  COMPLETED = 'COMPLETED'
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
