"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const boom_1 = require("@hapi/boom");
const typeorm_1 = require("typeorm");
const db_1 = require("@/utils/db");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const UsersProcesses_1 = require("@/repositories/UsersProcesses");
const users_processes_1 = require("@/@types/users-processes");
const rawHandler = async (event) => {
    console.log('Event: ', event);
    await db_1.createOrGetDBConnection();
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_1.UsersProcessesRepository);
    const { runId, newStatus } = event.body;
    const userProcess = await usersProcessesRepository.getByProcessRunId(runId);
    if (!userProcess)
        throw boom_1.notFound('usersProcess was not found');
    if (!Object.values(users_processes_1.PROCESS_STATUS).includes(newStatus)) {
        throw boom_1.notFound('New status is incorrect');
    }
    userProcess.setStatus(newStatus);
    if (newStatus === users_processes_1.PROCESS_STATUS.WARNING) {
        userProcess.setEndTime(new Date().toISOString());
        userProcess.setDuration();
    }
    await usersProcessesRepository.update(userProcess);
    console.log(`Set new status ${newStatus} to userProcess ${userProcess.id}`, new Date().toISOString(), new Date().getTime());
    return {
        statusCode: 200,
        body: userProcess
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map