import {EventEmitter, Injectable} from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SubnetMergerViewService {

  public refreshNDtsTable: EventEmitter<any> = new EventEmitter<any>();
  public refreshReportsTable: EventEmitter<any> = new EventEmitter<any>();

  constructor() {
  }
}
