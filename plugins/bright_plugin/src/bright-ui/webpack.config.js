const {shareAll, withModuleFederationPlugin} = require('@angular-architects/module-federation/webpack');

module.exports = withModuleFederationPlugin({

  name: 'bright-ui',

  exposes: {
    'UfmDevicesModule': './src/app/bright/packages/ufm-devices/ufm-devices.module.ts',
    'DevicesJobsViewModule': './src/app/bright/views/devices-jobs-view/devices-jobs-view.module.ts',
    'BrightConfigurationsViewModule': './src/app/bright/views/bright-configurations-view/bright-configurations-view.module.ts'
  },

  shared: {
    ...shareAll({singleton: true, strictVersion: false, requiredVersion: 'auto'}),
  },

});
