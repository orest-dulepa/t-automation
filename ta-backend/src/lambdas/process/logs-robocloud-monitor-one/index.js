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
const UsersProcesses_1 = require("@/repositories/UsersProcesses");
const robocorp_1 = require("@/http-clients/robocorp");
const processLogs_1 = require("@/utils/processLogs");
const rawHandler = async (event, context, callback) => {
    const { processId } = event;
    await db_1.createOrGetDBConnection();
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_1.UsersProcessesRepository);
    const userProcess = await usersProcessesRepository.getById(processId);
    if (!userProcess)
        return callback(null);
    const processRunId = userProcess.processRunId;
    const credentials = userProcess.process.credentials;
    const { robotRuns } = await robocorp_1.monitorRobocorp({
        processRunId,
        ...credentials,
    });
    const { id: robotRunsId } = robotRuns[0];
    await processLogs_1.processLogs(userProcess, robotRunsId);
    return callback(null);
};
exports.handler = middy_1.default(rawHandler).use(middlewares_1.doNotWaitForEmptyEventLoop());
//# sourceMappingURL=index.js.map