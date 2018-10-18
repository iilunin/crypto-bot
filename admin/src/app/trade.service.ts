
import {Subject} from 'rxjs';
import {Injectable} from '@angular/core';

export class TradeEvent {
  source: string;
  type: 'created' | 'updated';

  constructor(source, type) {
    this.source = source;
    this.type = type;
  }
}

@Injectable({ providedIn: 'root' })
export class TradeService {
  private eventAnouncementSource = new Subject<TradeEvent>();
  eventAnounces$ = this.eventAnouncementSource.asObservable();

  anounce(evt: TradeEvent): void {
    this.eventAnouncementSource.next(evt);
  }
}
