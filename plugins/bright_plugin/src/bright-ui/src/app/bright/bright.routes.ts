import { Routes } from '@angular/router';
import {BrightComponent} from "./bright.component";
import {DevicesJobsRoutes} from "./views/devices-jobs-view/devices-jobs.routes";
import {DevicesJobsViewComponent} from "./views/devices-jobs-view/devices-jobs-view.component";

export const BrightRoutes:Routes = [
    {
        path: 'bright',
        component: BrightComponent,
        children: [
          // ...DevicesJobsRoutes
          {
            path: 'device-jobs',
            component: DevicesJobsViewComponent,
          }
        ]
    }
];
