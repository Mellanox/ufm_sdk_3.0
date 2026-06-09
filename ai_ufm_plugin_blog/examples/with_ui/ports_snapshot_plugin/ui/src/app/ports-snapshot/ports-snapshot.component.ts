import { Component, OnInit } from '@angular/core';
import { PortsSnapshotService, PortsSummary } from './ports-snapshot.service';

@Component({
  selector: 'ufm-ports-snapshot',
  templateUrl: './ports-snapshot.component.html',
  styleUrls: ['./ports-snapshot.component.scss']
})
export class PortsSnapshotComponent implements OnInit {
  loading = true;
  error = '';
  summary?: PortsSummary;

  constructor(private service: PortsSnapshotService) {}

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.loading = true;
    this.error = '';
    this.service.getSummary().subscribe({
      next: value => {
        this.summary = value;
        this.loading = false;
      },
      error: err => {
        this.error = err?.message || 'Failed to load ports summary';
        this.loading = false;
      }
    });
  }
}
