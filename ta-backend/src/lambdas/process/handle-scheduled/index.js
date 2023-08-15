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
const scheduled_processes_1 = require("@/@types/scheduled-processes");
const ScheduledProcesses_1 = require("@/repositories/ScheduledProcesses");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const process_1 = require("@/@types/process");
const lambda = new aws_sdk_1.default.Lambda();
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const scheduledProcessesRepository = typeorm_1.getCustomRepository(ScheduledProcesses_1.ScheduledProcessesRepository);
    console.log('scheduledEvent', event);
    const { scheduledProcessId, changeStatusUrl } = event.Payload.Input;
    const scheduledProcess = await scheduledProcessesRepository.getById(scheduledProcessId);
    if (!scheduledProcess)
        return;
    if (scheduledProcess.status === scheduled_processes_1.SCHEDULED_PROCESS_STATUS.CANCELED)
        return;
    const dataForBot = [
        { name: 'Change Status Url', api_name: 'changeStatusUrl', value: changeStatusUrl, type: process_1.PROPERTY_TYPE.text },
    ];
    const lambdaParams = {
        FunctionName: process.env.START_PROCESS_LAMBDA_ARN,
        InvocationType: 'RequestResponse',
        Payload: JSON.stringify({
            processId: scheduledProcess.process.id,
            userId: scheduledProcess.user.id,
            meta: scheduledProcess.meta || [],
            dataForBot: dataForBot || [],
        }),
    };
    await lambda
        .invoke(lambdaParams)
        .promise()
        .catch((e) => console.log(e));
    await scheduledProcessesRepository.updateStatusById(scheduledProcessId, scheduled_processes_1.SCHEDULED_PROCESS_STATUS.SUCCEEDED);
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer());
//# sourceMappingURL=index.js.map