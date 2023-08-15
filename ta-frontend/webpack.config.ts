import path from 'path';
import HtmlWebpackPlugin from 'html-webpack-plugin';
import createStyledComponentsTransformer from 'typescript-plugin-styled-components';
import TsconfigPathsPlugin from 'tsconfig-paths-webpack-plugin';
import CopyWebpackPlugin from 'copy-webpack-plugin';
import { Configuration, EnvironmentPlugin } from 'webpack';
import { config } from 'dotenv';

config();

export default {
  mode: process.env.NODE_ENV,
  context: path.resolve(__dirname, 'src'),
  entry: {
    bundle: './index.tsx',
  },
  output: {
    publicPath: '/',
    filename: '[name].js',
    path: path.resolve(__dirname, 'build'),
  },
  devServer: {
    contentBase: path.join(__dirname, 'build'),
    inline: true,
    hot: true,
    port: Number(process.env.PORT) || 5000,
    publicPath: '/',
    host: '0.0.0.0',
    historyApiFallback: {
      index: '/',
    },
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx)?$/,
        loader: 'ts-loader',
        options: {
          getCustomTransformers: () => ({
            before: [createStyledComponentsTransformer()],
          }),
        },
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  resolve: {
    plugins: [new TsconfigPathsPlugin()],
    extensions: ['.js', '.ts', '.tsx'],
  },
  plugins: [
    new HtmlWebpackPlugin({ template: './html/index.html' }),
    new CopyWebpackPlugin({ patterns: [{ from: 'assets', to: 'assets', noErrorOnMissing: true }] }),
    new EnvironmentPlugin({ ...process.env }),
  ],
} as Configuration;
