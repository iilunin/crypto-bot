import { Directive, Input } from '@angular/core';
import { AbstractControl, NG_VALIDATORS, Validator } from '@angular/forms';

@Directive({
  selector: '[appSymbolValidator]',
  providers: [{provide: NG_VALIDATORS, useExisting: SymbolValidatorDirective, multi: true}]
})
export class SymbolValidatorDirective implements Validator {
  symbols: Set<string>;
  @Input('appSymbolValidator')
  set appSymbolValidator(val: string[]){
    this.symbols = new Set(val)
  }
  

  validate(control: AbstractControl): {[key: string]: any} | null {
    if (this.symbols) {
      return this.symbols.has(control.value) ? null : {'appSymbolValidator': {value: control.value}};
    }
    return null;
  }
}
