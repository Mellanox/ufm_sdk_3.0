import {Routes} from "@angular/router";
import {DevicesJobsViewComponent} from "./devices-jobs-view.component";

export const DevicesJobsRoutes:Routes = [
  {
    path: 'jobs',
    component: DevicesJobsViewComponent
  },
  {
    path: '**',
    redirectTo: 'jobs',
  }
];
