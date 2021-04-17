import { AfterViewInit, Component, OnInit, ViewChild } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { Balance } from '../balance';
import { BotApi } from '../botapi';

@Component({
  selector: 'app-balances',
  templateUrl: './balances.component.html',
  styleUrls: ['./balances.component.css']
})
export class BalancesComponent implements OnInit, AfterViewInit {

  @ViewChild(MatSort) sort: MatSort;
  
  balances: MatTableDataSource<Balance> = null;
  displayedColumns: string[] = ['sym', 'available', 'locked', 'total'];

  constructor(private api: BotApi) { }

  ngOnInit(): void {
 
  }

  ngAfterViewInit(): void {
    this.getBalances();
  }

  getBalances():void {
    this.api.getBalances(true).subscribe(
      res => {
        this.balances = new MatTableDataSource(res);
        this.balances.sort = this.sort;
        this.balances.sortingDataAccessor = (data, attribute) => data[attribute];
        this.balances.filterPredicate = this.balanceFilter;
        this.balances.filter = "+";
        // this.exchangeInfo.forEach(si => this.symbols.push(<string>si.s.toUpperCase()));
      }
    );
  }
  //  <input matInput (keyup)="applyFilter($event)" placeholder="Ex. ium" #input>
  
  balanceFilter(balance: Balance, filter: string): boolean {
    return (balance.avail + balance.locked) > 0;
  }
}
