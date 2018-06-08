import { TestBed, inject } from '@angular/core/testing';

import { BinanceService } from './binance.service';

describe('BinanceService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [BinanceService]
    });
  });

  it('should be created', inject([BinanceService], (service: BinanceService) => {
    expect(service).toBeTruthy();
  }));
});
