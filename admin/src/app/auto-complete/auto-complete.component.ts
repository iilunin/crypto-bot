import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  OnDestroy,
  ViewChild,
  ElementRef
} from "@angular/core";
import { FormControl, FormGroupDirective, NgForm } from "@angular/forms";
import { Observable, of, Subject } from "rxjs";
import {
  startWith,
  map,
  debounceTime,
  filter,
  switchMap,
  exhaustMap,
  tap,
  scan,
  takeWhile
} from "rxjs/operators";

import {ErrorStateMatcher} from '@angular/material/core';

/** Error when invalid control is dirty, touched, or submitted. */
export class MyErrorStateMatcher implements ErrorStateMatcher {
  isErrorState(control: FormControl | null, form: FormGroupDirective | NgForm | null): boolean {
    const isSubmitted = form && form.submitted;
    return !!(control && control.invalid && (control.dirty || control.touched || isSubmitted));
  }
}

export interface MatInput {
  id: number | string;
  name: string;
  sequence?: number;
}

@Component({
  selector: "app-auto-complete",
  templateUrl: "./auto-complete.component.html",
  styleUrls: ["./auto-complete.component.css"]
})
export class AutoCompleteComponent implements OnInit, OnDestroy {
  @ViewChild('validatedInput') validatedInputCtrl: ElementRef; 
  @Input() fieldCtrl: FormControl;
  smartList = [];

  @Input("smartList") set updateSmartList(data: any) {
    if (data && data.length) {
      this.smartList = data;
      this.getFilteredList();
    } else {
      this.smartList = [];
      this.getFilteredList();
    }
  }
  @Input() defaultValue?: any;
  @Input() placeHolder: string;
  @Input() appearance?: string;
  @Input() label?: string;
  @Input() model?: any;
  @Input() class?: string;

  @Output() optionSelected = new EventEmitter();
  toHighlight = "";
  filteredList: Observable<MatInput[]>;
  private nextPage$ = new Subject();

  constructor() {}

  ngOnInit(): void {
    this.getFilteredList();
  }

  /**
   * Result = of(currInputVal)
   */
  getChangedValOfInput() {
    const filter$ = this.fieldCtrl.valueChanges.pipe(
      startWith(""),
      debounceTime(400)
      // Note: If the option valye is bound to object, after selecting the option
      // Note: the value will change from string to {}. We want to perform search
      // Note: only when the type is string (no match)
      // filter(q => typeof q === 'string')
    );
    return filter$;
  }

  getFilteredList() {
    const filter$ = this.getChangedValOfInput();
    this.filteredList = filter$.pipe(
      switchMap(currInputVal => {
        // Note: Reset the page with every new seach text
        let currentPage = 1;
        return this.nextPage$.pipe(
          startWith(currentPage),
          // Note: Until the backend responds, ignore NextPage requests.
          exhaustMap(_ => this.getItems(currInputVal, currentPage)),
          tap(() => currentPage++),
          // Note: This is a custom operator because we also need the last emitted value.
          // Note: Stop if there are no more pages, or no results at all for the current search text.
          takeWhile(p => p.length > 0, true),
          scan(
            (allProducts, newProducts) => allProducts.concat(newProducts)
          )
        );
      })
    );
  }

  private getItems(startsWith: any, page: number): Observable<MatInput[]> {
    const take = 10;
    const skip = page > 0 ? (page - 1) * take : 0;
    let filterValue = "";
    // if ((startsWith || {}).name) {
    //   filterValue = (startsWith.name || "").toLowerCase();
    // } else {
    //   filterValue = (startsWith || "").toString().toLowerCase();
    // }

    if ((startsWith || {})) {
      filterValue = (startsWith || "").toUpperCase();
    } else {
      filterValue = (startsWith || "").toString().toUpperCase();
    }

    // console.log(this.smartList);
    
    const filtered = this.smartList.filter(
      // (option: any) => option.name.toLowerCase().indexOf(filterValue) >= 0
      (option: any) => option.toUpperCase().indexOf(filterValue) >= 0
    );
    return of(filtered.slice(skip, skip + take));
  }

  onSelect(event: any) {
    this.toHighlight = event.name;
    
    if(!this.fieldCtrl.errors){
      this.optionSelected.emit(this.validatedInputCtrl.nativeElement.value);
    }
  }

  onScroll() {
    this.nextPage$.next();
  }

    displayFn(data: any): string {
    // return data && data.name ? data.name : '';
    return data;
  }

  ngOnDestroy() {
    this.nextPage$.unsubscribe();
    if (this.optionSelected) {
      this.optionSelected.unsubscribe();
    }
  }
}
