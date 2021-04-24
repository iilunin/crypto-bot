import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AssetTableComponent } from './asset-table/asset-table.component';
import { BalancesComponent } from './balances/balances.component';
import {TradeDetailsComponent} from './trade-details/trade-details.component';


const appRoutes: Routes = [
  { path: '',   redirectTo: 'trades', pathMatch: 'full' },
  {path: 'balances',  component: BalancesComponent},
  {path: 'trades',  component: AssetTableComponent, children: [
      { path: ':id', component: TradeDetailsComponent, outlet: 'trade' }
    ] }

];

@NgModule({
  imports: [
    RouterModule.forRoot(appRoutes, { relativeLinkResolution: 'legacy' })
  ],
  exports: [
    RouterModule
  ]
})
export class TradesRoutingModule { }
