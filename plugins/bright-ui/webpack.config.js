//const shareAll = require('@angular-architects/module-federation/webpack');
const { shareAll } = require('@angular-architects/module-federation/webpack');
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");
const mf = require("@angular-architects/module-federation/webpack");
const path = require("path");
const share = mf.share;

const sharedMappings = new mf.SharedMappings();
sharedMappings.register(
  path.join(__dirname, 'tsconfig.json'),
  [/* mapped paths to share */]);

module.exports = {
  output: {
    uniqueName: "brightUi",
    publicPath: "http://localhost:4302/"
  },
  optimization: {
    runtimeChunk: false
  },
  resolve: {
    alias: {
      ...sharedMappings.getAliases(),
    }
  },
  experiments: {
    outputModule: true
  },
  plugins: [
    new ModuleFederationPlugin({
        //library: { type: "module" },

        // For remotes (please adjust)
         name: "brightUi",
         filename: "remoteEntry.js",
         exposes: {
           './brightModule': './src/app/bright/bright.module.ts',
        },

        // For hosts (please adjust)
        // remotes: {
        //     "mfe1": "http://localhost:3000/remoteEntry.js",

        // },

      //shared: {
        //...shareAll({singleton: true, strictVersion: false, requiredVersion: 'auto'}),
      //},

      /*shared: ["@angular/core",
        "@angular/common","@angular/router"]*/

      shared: share({
        "@angular/core": {singleton: true, strictVersion: false, requiredVersion: 'auto'},
        "@angular/common": {singleton: true, strictVersion: false, requiredVersion: 'auto'},
        "@angular/common/http": {singleton: true, strictVersion: false, requiredVersion: 'auto'},
        "@angular/router": {singleton: true, strictVersion: false, requiredVersion: 'auto'},

        ...sharedMappings.getDescriptors()
      })

    }),
      sharedMappings.getPlugin()
  ],
};
