import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {GeneralRouteModuleComponent} from "./general-route-module.component";

export const GeneralRouteModuleRoutes: Routes = [
  {
    path: 'general',
    component: GeneralRouteModuleComponent
  },
  /*{
    path: '**',
    redirectTo: 'general'
  }*/
];

@NgModule({
  imports: [RouterModule.forChild(GeneralRouteModuleRoutes)],
  exports: [RouterModule]
})
export class GeneralRouteModuleRoutingModule {
}
