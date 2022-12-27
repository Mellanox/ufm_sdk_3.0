import {Injector} from '@angular/core';

/**
 * Allows for retrieving singletons using `AppInjector.get(MyService)` (whereas
 * `ReflectiveInjector.resolveAndCreate(MyService)` would create a new instance
 * of the service).
 */
export let AppInjector: Injector;

/**
 * @desc Helper to set the exported {@link AppInjector}
 */
export function setAppInjector(injector: Injector) {
    if (AppInjector) {
        // Should not happen
        console.error('Programming error: AppInjector was already set');
    }
    else {
        AppInjector = injector;
    }
}