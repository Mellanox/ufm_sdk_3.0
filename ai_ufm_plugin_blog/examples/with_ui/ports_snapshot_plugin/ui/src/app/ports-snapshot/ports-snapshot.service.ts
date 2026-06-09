import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface PortsSummary {
  total_items: number;
  active_items: number;
  disabled_items: number;
  states: Record<string, number>;
  sample: Array<Record<string, unknown>>;
}

@Injectable({ providedIn: 'root' })
export class PortsSnapshotService {
  constructor(private http: HttpClient) {}

  getSummary(): Observable<PortsSummary> {
    return this.http.get<PortsSummary>('/ufmRest/plugin/ports_snapshot/summary');
  }
}
