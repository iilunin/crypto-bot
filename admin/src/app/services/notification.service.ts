import { Injectable } from "@angular/core";
import { Subject } from "rxjs";

export enum NotificatoinType {
    Regular,
    Warning,
    Alert
}

export class NotificationMessage {
    public contents: string;
    public action?: string;
    public type: NotificatoinType;

    constructor(contents: string, action?: string, type: NotificatoinType = NotificatoinType.Regular){
        this.contents = contents;
        this.action = action;
        this.type = type
    }
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
    public notification$: Subject<NotificationMessage> = new Subject();
}