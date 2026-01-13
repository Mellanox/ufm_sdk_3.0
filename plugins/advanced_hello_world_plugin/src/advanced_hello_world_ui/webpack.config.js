const { share, withModuleFederationPlugin } = require('@angular-architects/module-federation/webpack');

module.exports = withModuleFederationPlugin({

  name: 'hello_world_ui',

  exposes: {
    'GeneralRouteModule': './src/app/hello-world/general-route-module/general-route-module.module.ts',
    'HelloWorldModule': './src/app/hello-world/hello-world.module.ts',
    'DevicesDataTableModule': './src/app/hello-world/devices-data-table/devices-data-table.module.ts',
    'DeviceContextMenuModule': './src/app/hello-world/devices-context-menu/devices-context-menu.module.ts'
  },

  shared: share({
    "@angular/core": {singleton: true, strictVersion: true, requiredVersion: 'auto'},
    "@angular/common": {singleton: true, strictVersion: true, requiredVersion: 'auto'},
    "@angular/common/http": {singleton: true, strictVersion: true, requiredVersion: 'auto'},
    "@angular/router": {singleton: true, strictVersion: true, requiredVersion: 'auto'}
  }),

});
