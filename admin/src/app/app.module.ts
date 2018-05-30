import {AlertModule, ModalModule, TooltipModule} from 'ngx-bootstrap';
import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import { AssetTableComponent } from './asset-table/asset-table.component';
import {HttpClientModule} from '@angular/common/http';
import {WebsocketService} from './websocket.service';
import { TradeDetailsComponent } from './trade-details/trade-details.component';
import {TradesRoutingModule} from './trades-routing.module';

@NgModule({
  declarations: [
    AppComponent,
    AssetTableComponent,
    TradeDetailsComponent
  ],
  imports: [
    ModalModule.forRoot(),
    AlertModule.forRoot(),
    TooltipModule.forRoot(),
    BrowserModule,
    HttpClientModule,
    TradesRoutingModule
  ],
  providers: [WebsocketService],
  bootstrap: [AppComponent]
})
export class AppModule { }
