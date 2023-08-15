"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const typeorm_1 = require("typeorm");
const db_1 = require("@/utils/db");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const UsersProcesses_1 = require("@/repositories/UsersProcesses");
const Event_1 = require("@/repositories/Event");
const ProcessRunEventHandler_1 = __importDefault(require("./events-handlers/ProcessRunEventHandler"));
const RobotRunEventHandler_1 = __importDefault(require("./events-handlers/RobotRunEventHandler"));
const aws_sdk_1 = __importDefault(require("aws-sdk"));
const sqs = new aws_sdk_1.default.SQS();
const rawHandler = async (event) => {
    console.log('Event', event);
    const { body } = event;
    const stringifyChunk = JSON.stringify({
        processRunId: body.payload.processRunId,
        action: body.action,
    });
    const params = {
        MessageBody: stringifyChunk,
        QueueUrl: process.env.PROCESS_HANDLE_QUEUE_ARN,
        MessageGroupId: body.payload.processRunId,
    };
    await sqs.sendMessage(params).promise();
    await db_1.createOrGetDBConnection();
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_1.UsersProcessesRepository);
    const eventRepository = typeorm_1.getCustomRepository(Event_1.EventRepository);
    const handlers = [
        new ProcessRunEventHandler_1.default(),
        new RobotRunEventHandler_1.default(usersProcessesRepository, eventRepository),
    ];
    const handler = handlers.reduce((a, b) => {
        b.setNext(a);
        return b;
    });
    await handler.try(body).catch((e) => {
        console.log(e);
    });
    return {
        statusCode: 200,
        body: {},
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map