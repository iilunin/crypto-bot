export class TradeInfo {
  id: string;
  sym: string;
  avail: number;
  locked: number;
  price: number;
//  currPriceB?: number;
  btcVal: number;
  paused: boolean;
  buy: boolean;

  get balance(): number {
    return this.avail + this.locked;
  }

  constructor(init?: Partial<TradeInfo>){
    Object.assign(this, init);
  }
  // public setCurrPrice(bid, ask) {
  //   this.currPriceA = ask;
  //   this.currPriceB = bid;
  //   this.btcVal = this.currPriceA * (this.locked + this.avail);
  // }
}


