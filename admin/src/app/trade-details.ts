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
  constructor(init?: Partial<Target>) {
    Object.assign(this, init);
  }
  status: TradeStatus;
  id: number;
  date: string;
  price: string;
  vol: string;
  calculated_volume: string;
  smart: boolean;
  sl: string;
  best_price: string;
  isCompleted(): boolean { return this.status === TradeStatus.COMPLETED; }
}

export class ExitInfo {  
  smart: boolean;
  threshold: string;
  targets: Target[];
  constructor(init?: Partial<ExitInfo>) {

    Object.assign(this, init);
    
    this.targets = [];
    if(init?.targets){
      
      init?.targets.forEach(x => this.targets.push(new Target(x)));
    }
    if(!init?.threshold){
      this.threshold = 0.4.toString() + '%';
    }
  }
  
}

export class StopLoss {
  type: SLType = SLType.FIXED;
  threshold = '5%';
  initial_target: Target;
  isFixed(): boolean { return this.type === SLType.FIXED; }
 
  get isTrailing(): boolean { return this.type === SLType.TRAILING; }
  set isTrailing(value: boolean) { this.type = value ? SLType.TRAILING:SLType.FIXED;}
  
  constructor() {
    this.initial_target = new Target();
    this.initial_target.vol = '100%';
  }
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

  constructor(create_new: boolean = false, init?: Partial<TradeDetails>) {
    Object.assign(this, init);
    if (init?.exit){
      this.exit = new ExitInfo(init.exit);
    }
    if (init?.entry){
      this.entry = new Entry(init.entry);
    }

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
  
  constructor(init?: Partial<EntryTarget>) {
    Object.assign(this, init);
  }

  status: TradeStatus;
  price: string;
  vol: string;

  isCompleted(): boolean { return this.status === TradeStatus.COMPLETED; }
}

export class Entry {

  side: 'BUY' | 'SELL' = 'BUY';
  targets: EntryTarget[];
  smart: boolean;

  constructor(init?: Partial<Entry>, sell?: boolean) {
    
    Object.assign(this, init);
    
    if(init?.targets){
      this.targets = [];
      init?.targets.forEach(x => this.targets.push(new EntryTarget(x)));
    }
    
    this.setIsSell(sell);
  }

  getTarget(): EntryTarget {
    return this.targets && this.targets.length > 0? this.targets[0] : null;
  }

  

  isBuy(): boolean { return this.side === 'BUY'; }
  isSell(): boolean { return !this.isBuy(); }
  setIsSell(sell: boolean): void {
    if (sell) { this.side = 'SELL'; } else { this.side = 'BUY'; }
  }
}



export enum TradeDetailMode {
  View,
  Edit,
  Create
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
