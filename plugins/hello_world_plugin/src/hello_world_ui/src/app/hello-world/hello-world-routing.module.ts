import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {GeneralRouteModuleComponent} from "./general-route-module/general-route-module.component";
import {HelloWorldComponent} from "./hello-world.component";
import {GeneralRouteModuleRoutes} from "./general-route-module/general-route-module-routing.module";

const routes: Routes = [
  {
    path: "hello_world",
    component: HelloWorldComponent,
    children:[
      ...GeneralRouteModuleRoutes
    ]
  },
  {
    path: "**",
    redirectTo: "hello_world/general"
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HelloWorldRoutingModule { }
