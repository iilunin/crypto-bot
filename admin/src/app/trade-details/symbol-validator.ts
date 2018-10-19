import { Directive, Input, OnChanges, SimpleChanges } from '@angular/core';
import { AbstractControl, NG_VALIDATORS, Validator, ValidatorFn, Validators } from '@angular/forms';

@Directive({
  selector: '[appSymbolValidator]',
  providers: [{provide: NG_VALIDATORS, useExisting: SymbolValidatorDirective, multi: true}]
})
export class SymbolValidatorDirective implements Validator {
  @Input('appSymbolValidator')
  appSymbolValidator: Set<string>;

  validate(control: AbstractControl): {[key: string]: any} | null {
    // return this.appSymbolValidator ? symbolValidator(new RegExp(this.appSymbolValidator, 'i'))(control)
    //   : null;
    if (this.appSymbolValidator) {
      return this.appSymbolValidator.has(control.value) ? null : {'appSymbolValidator': {value: control.value}};
    }
    return null;
  }
}
