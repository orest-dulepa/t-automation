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
const boom_1 = require("@hapi/boom");
const moment_1 = __importDefault(require("moment"));
const db_1 = require("@/utils/db");
const ScheduledProcesses_1 = require("@/repositories/ScheduledProcesses");
const Process_1 = require("@/repositories/Process");
const ScheduledProcess_1 = require("@/entities/ScheduledProcess");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const auth_parser_1 = require("@/middlewares/auth-parser");
const stepFunctions = new aws_sdk_1.default.StepFunctions();
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const scheduledProcessesRepository = typeorm_1.getCustomRepository(ScheduledProcesses_1.ScheduledProcessesRepository);
    const processRepository = typeorm_1.getCustomRepository(Process_1.ProcessRepository);
    const { body, pathParameters, requestContext } = event;
    const { meta, timestamp } = body;
    const { id } = pathParameters;
    const { authorizer: user } = requestContext;
    const processToRun = await processRepository.getById(id);
    if (!processToRun)
        throw boom_1.notFound("process wasn't found");
    console.log('timestamp', timestamp);
    const scheduledProcess = await scheduledProcessesRepository.insert(new ScheduledProcess_1.ScheduledProcess(meta, moment_1.default(timestamp).valueOf(), user, processToRun, user.organization));
    console.log('scheduledProcess', scheduledProcess);
    const payload = {
        stateMachineArn: process.env.STATE_MACHINE_ARN,
        input: JSON.stringify({
            timestamp,
            body: {
                scheduledProcessId: scheduledProcess.id,
                changeStatusUrl: `https://${requestContext.domainName}/${requestContext.stage}/processes/change-status`,
            },
        }),
    };
    console.log('payload', payload);
    await stepFunctions
        .startExecution(payload)
        .promise()
        .catch((e) => console.log(e));
    return {
        statusCode: 201,
        body: {},
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(auth_parser_1.authParser())
    .use(middlewares_1.jsonBodyParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map