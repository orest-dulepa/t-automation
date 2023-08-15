"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const aws_sdk_1 = __importDefault(require("aws-sdk"));
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const typeorm_1 = require("typeorm");
const db_1 = require("@/utils/db");
const UsersProcesses_1 = require("@/repositories/UsersProcesses");
const lambda = new aws_sdk_1.default.Lambda();
const rawHandler = async (event, context, callback) => {
    await db_1.createOrGetDBConnection();
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_1.UsersProcessesRepository);
    const processingProcesses = await usersProcessesRepository.getProcessing();
    console.log('processingProcesses: ', processingProcesses);
    for (const processingProcess of processingProcesses) {
        const lambdaParams = {
            FunctionName: process.env.LOGS_ROBOCLOUD_MONITOR_ONE_LAMBDA_ARN,
            InvocationType: 'Event',
            Payload: JSON.stringify({
                processId: processingProcess.id,
            }),
        };
        lambda.invoke(lambdaParams).promise().catch((e) => console.log(e));
    }
    return callback(null);
};
exports.handler = middy_1.default(rawHandler).use(middlewares_1.doNotWaitForEmptyEventLoop());
//# sourceMappingURL=index.js.map