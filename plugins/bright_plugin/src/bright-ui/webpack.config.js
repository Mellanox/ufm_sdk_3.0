const {shareAll, withModuleFederationPlugin} = require('@angular-architects/module-federation/webpack');

module.exports = withModuleFederationPlugin({

  name: 'bright-ui',

  exposes: {
    './Component': './src/app/app.component.ts',
    'UfmDevicesModule': './src/app/bright/packages/ufm-devices/ufm-devices.module.ts'
  },

  shared: {
    ...shareAll({singleton: true, strictVersion: false, requiredVersion: 'auto'}),
  },

});
