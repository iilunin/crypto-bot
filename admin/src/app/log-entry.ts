export class LogEntry {
    
    d: Date;
    l: string;
    t: string;
    o: string;

    constructor(init?: Partial<LogEntry>){
        Object.assign(this, init)
    }

    get date(): Date{
        return this.d;
    }

    get level(): string{
        return this.l;
    }

    get originator(): string{
        return this.o;
    }

    get text(): string{
        return this.t;
    }
}
