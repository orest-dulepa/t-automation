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
const UsersProcesses_1 = require("@/repositories/UsersProcesses");
const users_processes_1 = require("@/@types/users-processes");
const rawHandler = async (event) => {
    const detailType = event['detail-type'];
    const AWSStatus = event.detail.status;
    const processRunId = JSON.parse(event.detail.input).processRunId;
    console.log('Event: ', event);
    console.log('Type: ', detailType);
    console.log('AWSStatus: ', AWSStatus);
    console.log('ProcessRunId: ', processRunId);
    if (detailType !== 'Step Functions Execution Status Change')
        return;
    await db_1.createOrGetDBConnection();
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_1.UsersProcessesRepository);
    const userProcess = await usersProcessesRepository.getByProcessRunId(processRunId);
    console.log('Before status:', userProcess === null || userProcess === void 0 ? void 0 : userProcess.status);
    if ((userProcess === null || userProcess === void 0 ? void 0 : userProcess.status) &&
        (userProcess.status !== users_processes_1.PROCESS_STATUS.PROCESSING && userProcess.status !== users_processes_1.PROCESS_STATUS.INITIALIZED))
        return;
    if (!userProcess)
        throw boom_1.notFound('UsersProcess was not found');
    const newStatus = users_processes_1.AWS_PROCESS_STATUS_TO_STANDART_STATUS[AWSStatus];
    userProcess.setStatus(newStatus);
    console.log(`Set new status ${newStatus} to userProcess ${userProcess.id}`);
    if (AWSStatus !== users_processes_1.AWS_PROCESS_STATUS.RUNNING) {
        userProcess.setEndTime(new Date().toISOString());
        userProcess.setDuration();
        console.log(`Set endTime and duration to userProcess ${userProcess.id}`);
    }
    await usersProcessesRepository.update(userProcess);
};
exports.handler = middy_1.default(rawHandler).use(middlewares_1.doNotWaitForEmptyEventLoop());
//# sourceMappingURL=index.js.map