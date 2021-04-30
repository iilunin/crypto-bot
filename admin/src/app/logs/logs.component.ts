import { Component, OnInit } from '@angular/core';
import { BotApi } from '../botapi';

@Component({
  selector: 'app-logs',
  templateUrl: './logs.component.html',
  styleUrls: ['./logs.component.css']
})
export class LogsComponent implements OnInit {

  logContents: String[];

  constructor(private api: BotApi) { }

  ngOnInit(): void {
    this.refreshLogs();  
  }

  refreshLogs(): void {
    this.api.getRecentLogFileContents().subscribe(r => {
      if (r){
        this.logContents = r.trim().split('\n').reverse();
      }
    })
  }

}
