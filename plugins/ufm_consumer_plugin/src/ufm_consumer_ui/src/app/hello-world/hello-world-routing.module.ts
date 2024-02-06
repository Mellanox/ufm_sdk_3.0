import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {GeneralRouteModuleComponent} from "./general-route-module/general-route-module.component";
import {HelloWorldComponent} from "./hello-world.component";
import {GeneralRouteModuleRoutes} from "./general-route-module/general-route-module-routing.module";

const routes: Routes = [
  {
    path: "ufm_consumer",
    component: HelloWorldComponent,
    children:[
      ...GeneralRouteModuleRoutes
    ]
  },
  {
    path: "**",
    redirectTo: "ufm_consumer/general"
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HelloWorldRoutingModule { }
