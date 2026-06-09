import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { PortsSnapshotModule } from './app/ports-snapshot/ports-snapshot.module';

platformBrowserDynamic().bootstrapModule(PortsSnapshotModule).catch(err => console.error(err));
