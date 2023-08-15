import path from 'path';
import slsw from 'serverless-webpack';
import nodeExternals from 'webpack-node-externals';
import type { Configuration } from 'webpack';
import TsconfigPathsPlugin from 'tsconfig-paths-webpack-plugin';
import TerserPlugin from 'terser-webpack-plugin';

const config: Configuration = {
  target: 'node',
  mode: slsw.lib.webpack.isLocal ? 'development' : 'production',
  devtool: slsw.lib.webpack.isLocal ? 'cheap-module-eval-source-map' : 'source-map',
  context: __dirname,
  entry: slsw.lib.entries,
  output: {
    libraryTarget: 'commonjs',
    path: path.join(__dirname, '.webpack'),
    filename: '[name].js',
  },
  resolve: {
    plugins: [new TsconfigPathsPlugin()],
    extensions: ['.mjs', '.json', '.ts'],
    symlinks: false,
    cacheWithContext: false,
  },
  module: {
    rules: [
      {
        test: /\.(tsx?)$/,
        loader: 'ts-loader',
        exclude: [
          [
            path.resolve(__dirname, 'node_modules'),
            path.resolve(__dirname, '.serverless'),
            path.resolve(__dirname, '.webpack'),
          ],
        ],
        options: {
          transpileOnly: true,
          experimentalWatchApi: true,
        },
      },
    ],
  },
  optimization: {
    minimizer: [
      new TerserPlugin({
        parallel: true,
        terserOptions: {
          // Required for TypeORM migrations
          keep_classnames: true,
          sourceMap: true,
        },
      }),
    ],
  },
  plugins: [],
  externals: [nodeExternals()],
};

module.exports = config;
