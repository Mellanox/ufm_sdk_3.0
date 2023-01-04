import {Routes} from '@angular/router';
import {BrightConfigurationsViewComponent} from './bright-configurations-view.component';

export const BrightConfigurationsRoutes: Routes = [
  {
    path: 'configurations',
    component: BrightConfigurationsViewComponent
  },
  {
    path: '**',
    redirectTo: 'configurations',
  }
];
