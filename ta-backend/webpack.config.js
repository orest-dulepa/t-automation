"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const path_1 = __importDefault(require("path"));
const serverless_webpack_1 = __importDefault(require("serverless-webpack"));
const webpack_node_externals_1 = __importDefault(require("webpack-node-externals"));
const tsconfig_paths_webpack_plugin_1 = __importDefault(require("tsconfig-paths-webpack-plugin"));
const terser_webpack_plugin_1 = __importDefault(require("terser-webpack-plugin"));
const config = {
    target: 'node',
    mode: serverless_webpack_1.default.lib.webpack.isLocal ? 'development' : 'production',
    devtool: serverless_webpack_1.default.lib.webpack.isLocal ? 'cheap-module-eval-source-map' : 'source-map',
    context: __dirname,
    entry: serverless_webpack_1.default.lib.entries,
    output: {
        libraryTarget: 'commonjs',
        path: path_1.default.join(__dirname, '.webpack'),
        filename: '[name].js',
    },
    resolve: {
        plugins: [new tsconfig_paths_webpack_plugin_1.default()],
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
                        path_1.default.resolve(__dirname, 'node_modules'),
                        path_1.default.resolve(__dirname, '.serverless'),
                        path_1.default.resolve(__dirname, '.webpack'),
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
            new terser_webpack_plugin_1.default({
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
    externals: [webpack_node_externals_1.default()],
};
module.exports = config;
//# sourceMappingURL=webpack.config.js.map