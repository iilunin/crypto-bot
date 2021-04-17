export class Balance {
    sym: string;
    avail: number;
    locked: number;

    get total(): number {
        return this.avail + this.locked;
    }

    constructor(init?: Partial<Balance>){
        Object.assign(this, init)
    }
}
