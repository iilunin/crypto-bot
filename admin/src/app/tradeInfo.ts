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

  // public setCurrPrice(bid, ask) {
  //   this.currPriceA = ask;
  //   this.currPriceB = bid;
  //   this.btcVal = this.currPriceA * (this.locked + this.avail);
  // }
}


