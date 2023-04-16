import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {NdtComponent} from "./ndt.component";
import {subnetMergerViewRoutes} from "./views/subnet-merger-view/subnet-merger-view.routes";

const routes: Routes = [
  {
    path: 'ndt',
    component: NdtComponent,
    children: [
      ...subnetMergerViewRoutes
    ]
  }, {
    path: '**',
    redirectTo: 'ndt/subnet-merger'
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class NdtRoutingModule {
}
