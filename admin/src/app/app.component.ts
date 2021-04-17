import { Component } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AuthService } from './auth.service';
import { NotificationService, NotificatoinType } from './services/notification.service'

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})

export class AppComponent {
  title = 'Crypto Bot';

  constructor(
    private notificationService: NotificationService, 
    private snackBar: MatSnackBar,
    public auth: AuthService
  ) {
    this.notificationService.notification$.subscribe(message => {
      
      console.log(message)
      this.snackBar.open(message.contents, message.action, 
        { 
          duration: 3000,
          panelClass: [this.getPanelClass(message.type)]});
          // panelClass: ["blue-snackbar"]});
    });
  }

  private getPanelClass(type: NotificatoinType): string {
    switch(type){
      case NotificatoinType.Regular:
        return 'snackbar-primary';
      case NotificatoinType.Warning:
        return 'snackbar-warning';
      case NotificatoinType.Alert:
        return 'snackbar-alarm'
      default:
        return '';
    }
    
  }
}
