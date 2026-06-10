import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { PortsSnapshotComponent } from './ports-snapshot.component';

@NgModule({
  declarations: [PortsSnapshotComponent],
  imports: [
    CommonModule,
    HttpClientModule,
    RouterModule.forChild([
      { path: '', component: PortsSnapshotComponent, pathMatch: 'full' },
      { path: 'overview', component: PortsSnapshotComponent },
      { path: '**', component: PortsSnapshotComponent }
    ])
  ],
  exports: [PortsSnapshotComponent]
})
export class PortsSnapshotModule {}
