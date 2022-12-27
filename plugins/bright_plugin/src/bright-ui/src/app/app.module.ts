import {Injector, NgModule} from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import {BrightModule} from "./bright/bright.module";
import {RouterModule} from "@angular/router";
import {routes} from "./app.routes";
import {Constants} from "./constants/constants";

@NgModule({
  declarations: [
    AppComponent,
  ],
  imports: [
    BrowserModule,
    RouterModule.forRoot(routes),
    BrightModule
  ],
  providers: [Constants],
  bootstrap: [AppComponent]
})
export class AppModule {

  constructor() {
  }

}
