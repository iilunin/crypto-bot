import {AfterContentInit, ChangeDetectorRef, Component, ElementRef, Inject, OnInit, Optional, TemplateRef, ViewChild} from '@angular/core';
import {Location} from '@angular/common';
import {ActivatedRoute, ParamMap, Router} from '@angular/router';
import {BotApi} from '../botapi';
import {BinanceService, BinancePriceResult} from '../binance.service';
import {switchMap} from 'rxjs/operators';
import {Mode, TradeDetailMode, TradeDetails} from '../trade-details';
import {Observable} from 'rxjs';
// import {BsModalService} from 'ngx-bootstrap/modal';
// import {BsModalRef} from 'ngx-bootstrap/modal/bs-modal-ref.service';
import {MatDialog, MatDialogRef, MAT_DIALOG_DATA} from '@angular/material/dialog';
import {TradeEvent, TradeService} from '../trade.service';
import { FormControl, Validators } from '@angular/forms';
import {map, startWith} from 'rxjs/operators';
import { AutoCompleteComponent } from '../auto-complete/auto-complete.component';
import { SymbolValidatorDirective } from './symbol-validator';
import { reduceEachTrailingCommentRange } from 'typescript';

@Component({
  selector: 'app-trade-details',
  templateUrl: './trade-details.component.html',
  styleUrls: ['./trade-details.component.css']
})
export class TradeDetailsComponent implements OnInit {


  private tradeDetailMode = TradeDetailMode;
  @ViewChild('symAutoComplete') autoComplete: AutoCompleteComponent;

  // trade$: Observable<TradeDetails>;
  trade: TradeDetails;
  
  tradeId: string;
  mode: Mode;
  // trade: TradeDetails;
  priceInfo: BinancePriceResult;

  exchangeInfo: any[];
  symbols: string[] = [];

  myControl = new FormControl('', Validators.required);
  
  // private config = {
  //   class: 'modal-lg',
  //   keyboard: false,
  //   ignoreBackdropClick: true
  // };
  // modalRef: MatDialogRef<any, any>;

  constructor(@Inject(MAT_DIALOG_DATA) public data: {mode: Mode, id: string},
              private dialogRef: MatDialogRef<TradeDetailsComponent>,
              private route: ActivatedRoute,
              private changeDetector: ChangeDetectorRef,
              private router: Router,
              private location: Location,
              private api: BotApi,
              private binance: BinanceService,
              private tradeService: TradeService
              ) {
    this.mode = data.mode;
    this.tradeId = data.id
    // this.route.paramMap.subscribe(params => this.mode = new Mode(<TradeDetailMode>params.get('mode')));
  }

  static openDialog(dialog: MatDialog, mode: Mode,  tradeId: string) {
    let tdDialog = dialog.open(TradeDetailsComponent, {
      data: { mode: mode, id: tradeId },
      width: '800px'
    });
    // tdDialog.afterClosed().subscribe(result => {
    //   console.log(`Dialog result: ${result}`);
    // });  
  }

  ngOnInit() {
    setTimeout(this.init.bind(this), 0);
  }

  private init() {

    if (this.mode.isCreate()) {
      this.trade = new TradeDetails(true);
      this.api.getExchangeInfo().subscribe(
        res => {
          this.exchangeInfo = res;
          // this.symbols = [];
          this.exchangeInfo.forEach(si => this.symbols.push(<string>si.s.toUpperCase()));
          this.autoComplete.smartList = this.symbols.sort();
        }
      );
    } else {
      this.exchangeInfo = [];
      this.api.getActiveTradeInfo(this.tradeId).subscribe(trade => this.trade = trade)
    }
  }

  confirm() {
    console.log('confirm')
    if(!this.myControl.errors && this.dialogRef)
      this.dialogRef.close()
    return;
    this.api.addTrade(this.trade).subscribe(
      res => {
        if (this.mode.isCreate()) {
          this.tradeService.anounce(new TradeEvent('TradeDeatails', 'created'));
        }
      },
      err => console.log(err)
    );
  }

  // decline() {
  //   this.closeModal();
  // }

  // closeModal() {
  //   // this.modalRef.close()
  //   // this.router.navigate(['/trades']);
  // }

  onPriceUpdate(price: BinancePriceResult): void {
    this.priceInfo = price;
  }

  onSymbolSelected(symbol) {
    if (typeof(symbol) !== 'string')
      return;

      if (this.mode.isCreate()) {
      // if (this.trade.symbol !== symbol) {
        // query binance prices
        this.binance.getPrice(symbol).subscribe(this.onPriceUpdate.bind(this));
      // }
    }
  }
}
