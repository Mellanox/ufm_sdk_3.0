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
      { path: 'overview', component: PortsSnapshotComponent },
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
      { path: '**', redirectTo: 'overview' }
    ])
  ],
  exports: [PortsSnapshotComponent]
})
export class PortsSnapshotModule {}
