import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';

import {AppRoutingModule} from './app-routing.module';
import {AppComponent} from './app.component';
import {NdtModule} from "./ndt/ndt.module";

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    NdtModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {
}
