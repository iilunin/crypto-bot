import { Component } from '@angular/core';
import { MatIconRegistry } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DomSanitizer } from '@angular/platform-browser';
import { AuthService } from './auth.service';
import { BotApi } from './botapi';
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
    public auth: AuthService,
    private matIconRegistry: MatIconRegistry,
    private domSanitizer: DomSanitizer,
    private bot: BotApi
  ) {
    this.notificationService.notification$.subscribe(message => {
      
      this.snackBar.open(message.contents, message.action, 
        { 
          duration: 3000,
          panelClass: [this.getPanelClass(message.type)]});
          // panelClass: ["blue-snackbar"]});
    });
    
    this.matIconRegistry.addSvgIcon(  
      'my_git', domSanitizer.bypassSecurityTrustResourceUrl(`${this.bot.API_URL}/proxy/icon`)
    );
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
