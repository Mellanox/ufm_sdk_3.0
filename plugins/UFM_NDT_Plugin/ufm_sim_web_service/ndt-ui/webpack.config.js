const {shareAll, withModuleFederationPlugin} = require('@angular-architects/module-federation/webpack');

module.exports = withModuleFederationPlugin({

  name: 'ndt-ui',

  exposes: {
    'NdtModule': './src/app/ndt/ndt.module.ts',
  },

  shared: {
    ...shareAll({singleton: true, strictVersion: false, requiredVersion: 'auto'}),
  },

});
