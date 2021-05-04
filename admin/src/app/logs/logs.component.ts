import { AfterViewInit, Component, OnInit, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { BotApi } from '../botapi';
import { LogEntry } from '../log-entry';

@Component({
  selector: 'app-logs',
  templateUrl: './logs.component.html',
  styleUrls: ['./logs.component.css']
})
export class LogsComponent implements OnInit, AfterViewInit {

  logs: LogEntry[];
  dataSource: MatTableDataSource<LogEntry> = new MatTableDataSource<LogEntry>();
  limit: number = 1000;
  @ViewChild(MatPaginator) paginator: MatPaginator;
  @ViewChild(MatSort) sort: MatSort;


  constructor(private api: BotApi) { }
  ngAfterViewInit(): void {
    this.refreshLogs(); 
    console.log(this.paginator);
  }

  ngOnInit(): void {
    // this.refreshLogs();  
  }

  refreshLogs(): void {
    this.logs = null;
    this.api.getRecentLogFileContents(this.limit).subscribe(r => {
      if (r){
        this.logs = r;
        this.dataSource = new MatTableDataSource<LogEntry>(this.logs);
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
      }
    })
  }

  getClipboard(): string {
    let cb = ''
    
    if (this.logs){
      this.logs.forEach(l=> {
        cb += `${l.d.toLocaleString()} [${l.l}] [${l.o}]: ${l.t}\n`
      })
    }

    return cb
  }

}
