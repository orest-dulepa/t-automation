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
const db_1 = require("@/utils/db");
const users_processes_1 = require("@/@types/users-processes");
const role_1 = require("@/@types/role");
const UsersProcesses_1 = require("@/repositories/UsersProcesses");
const Event_1 = require("@/repositories/Event");
const Log_1 = require("@/repositories/Log");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const auth_parser_1 = require("@/middlewares/auth-parser");
const s3 = new aws_sdk_1.default.S3();
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_1.UsersProcessesRepository);
    const eventRepository = typeorm_1.getCustomRepository(Event_1.EventRepository);
    const logRepository = typeorm_1.getCustomRepository(Log_1.LogRepository);
    const { id: processId } = event.pathParameters;
    const { authorizer: user } = event.requestContext;
    const { id: userId, organization, role } = user;
    const { id: organizationId, name: organizationName } = organization;
    const { id: roleId } = role;
    const isManager = roleId === role_1.ROLE.MANAGER;
    const isAdmin = (roleId === role_1.ROLE.ADMIN && organizationName === 'ta');
    const userProcess = await usersProcessesRepository.getById(processId);
    if (!userProcess)
        throw boom_1.notFound('process wasn\'t found');
    const isUserProcessOwner = Number(userId) === Number(userProcess.user.id);
    const isOrganizationProcessOwner = Number(organizationId) === Number(userProcess.organization.id);
    if (!isAdmin && !isOrganizationProcessOwner)
        throw boom_1.forbidden('process doesn\'t belong to user organization');
    if (!isAdmin && !isManager && !isUserProcessOwner)
        throw boom_1.forbidden('process doesn\'t belong to user');
    const { Contents } = await s3
        .listObjectsV2({
        Bucket: process.env.BUCKET_NAME,
        Prefix: userProcess.processRunId,
        FetchOwner: false,
    })
        .promise();
    const artifacts = (Contents === null || Contents === void 0 ? void 0 : Contents.map(({ Key: key, Size: size }) => ({ key, size }))) || [];
    const events = await eventRepository.getAllByUserProcessId(userProcess.id);
    const log = await logRepository.getByUserProcessId(userProcess.id);
    const mappedEvents = events.map(({ seqNo, eventType, timeStamp }) => ({
        seqNo,
        eventType,
        timeStamp,
    }));
    if (events.length === 0) {
        mappedEvents.push({
            seqNo: '1',
            eventType: 'TA Logger event: Starting',
            timeStamp: userProcess.startTime || '',
        });
    }
    if (mappedEvents.length === 1 && userProcess.endTime) {
        const finalEvent = { seqNo: '2', eventType: '', timeStamp: '' };
        if (userProcess.status === users_processes_1.PROCESS_STATUS.FAILED) {
            finalEvent.eventType = 'TA Logger event: Failed';
        }
        if (userProcess.status === users_processes_1.PROCESS_STATUS.FINISHED) {
            finalEvent.eventType = 'TA Logger event: Finishing';
        }
        finalEvent.timeStamp = userProcess.endTime;
        mappedEvents.push(finalEvent);
    }
    return {
        statusCode: 200,
        body: {
            ...userProcess,
            artifacts,
            logs: (log === null || log === void 0 ? void 0 : log.text) || '',
            events: mappedEvents,
        },
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(auth_parser_1.authParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map