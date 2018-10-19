import {AlertModule, ButtonsModule, CollapseModule, ModalModule, TooltipModule, TypeaheadModule} from 'ngx-bootstrap';
import {BrowserModule} from '@angular/platform-browser';
import {CUSTOM_ELEMENTS_SCHEMA, NgModule} from '@angular/core';

import {AppComponent} from './app.component';
import {AssetTableComponent} from './asset-table/asset-table.component';
import {HTTP_INTERCEPTORS, HttpClientModule, HttpInterceptor} from '@angular/common/http';
import {WebsocketService} from './websocket.service';
import {TradeDetailsComponent} from './trade-details/trade-details.component';
import {TradesRoutingModule} from './trades-routing.module';
import {FormsModule} from '@angular/forms';
import {ExitDetailsComponent} from './trade-details/exit-details.component';
import {SLDetailsComponent} from './trade-details/sl-details.component';
import {SymbolValidatorDirective} from './trade-details/symbol-validator';
import {AuthInterceptor} from './auth.interceptor';
import { LogInComponent } from './log-in/log-in.component';

// const schemas: any[] = [];
// schemas.push(CUSTOM_ELEMENTS_SCHEMA);

@NgModule({
  declarations: [
    AppComponent,
    AssetTableComponent,
    TradeDetailsComponent,
    ExitDetailsComponent,
    SLDetailsComponent,
    SymbolValidatorDirective,
    LogInComponent
  ],
  imports: [
    // CollapseModule.forRoot(),
    TypeaheadModule.forRoot(),
    ButtonsModule.forRoot(),
    ModalModule.forRoot(),
    AlertModule.forRoot(),
    TooltipModule.forRoot(),
    BrowserModule,
    HttpClientModule,
    TradesRoutingModule,
    FormsModule
  ],
  providers: [WebsocketService,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    }],
  bootstrap: [AppComponent]
  // schemas: schemas
})
export class AppModule {
}
