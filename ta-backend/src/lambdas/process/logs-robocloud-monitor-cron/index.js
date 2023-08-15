"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const aws_sdk_1 = __importDefault(require("aws-sdk"));
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const sleep_1 = require("@/utils/sleep");
const lambda = new aws_sdk_1.default.Lambda();
const rawHandler = async (event, context, callback) => {
    let INVOCATION_COUNT = 0;
    while (true) {
        console.log('INVOCATION_COUNT', INVOCATION_COUNT);
        if (INVOCATION_COUNT >= 23) {
            return callback(null);
        }
        const lambdaParams = {
            FunctionName: process.env.LOGS_ROBOCLOUD_MONITOR_ALL_LAMBDA_ARN,
            InvocationType: 'Event',
        };
        lambda.invoke(lambdaParams).promise().catch((e) => console.log(e));
        INVOCATION_COUNT++;
        await sleep_1.sleep(2500);
    }
};
exports.handler = middy_1.default(rawHandler).use(middlewares_1.doNotWaitForEmptyEventLoop());
//# sourceMappingURL=index.js.map