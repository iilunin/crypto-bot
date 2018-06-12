import {AlertModule, ButtonsModule, CollapseModule, ModalModule, TooltipModule} from 'ngx-bootstrap';
import {BrowserModule} from '@angular/platform-browser';
import {CUSTOM_ELEMENTS_SCHEMA, NgModule} from '@angular/core';

import {AppComponent} from './app.component';
import {AssetTableComponent} from './asset-table/asset-table.component';
import {HttpClientModule} from '@angular/common/http';
import {WebsocketService} from './websocket.service';
import {TradeDetailsComponent} from './trade-details/trade-details.component';
import {TradesRoutingModule} from './trades-routing.module';
import {FormsModule} from '@angular/forms';
import {ExitDetailsComponent} from './trade-details/exit-details.component';
import {SLDetailsComponent} from './trade-details/sl-details.component';

// const schemas: any[] = [];
// schemas.push(CUSTOM_ELEMENTS_SCHEMA);

@NgModule({
  declarations: [
    AppComponent,
    AssetTableComponent,
    TradeDetailsComponent,
    ExitDetailsComponent,
    SLDetailsComponent
  ],
  imports: [
    // CollapseModule.forRoot(),
    ButtonsModule.forRoot(),
    ModalModule.forRoot(),
    AlertModule.forRoot(),
    TooltipModule.forRoot(),
    BrowserModule,
    HttpClientModule,
    TradesRoutingModule,
    FormsModule
  ],
  providers: [WebsocketService],
  bootstrap: [AppComponent]
  // schemas: schemas
})
export class AppModule {
}
