"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const typeorm_1 = require("typeorm");
const users_processes_1 = require("@/@types/users-processes");
const db_1 = require("@/utils/db");
const UsersProcesses_1 = require("@/repositories/UsersProcesses");
const sqs_body_parse_1 = require("@/middlewares/sqs-body-parse");
const robocorp_1 = require("@/http-clients/robocorp");
const processArtifacts_1 = require("@/utils/processArtifacts");
const robocloud_action_1 = require("@/@types/robocloud-action");
const rawHandler = async (event, context, callback) => {
    const { Records } = event;
    const [{ body: processLog }] = Records;
    const { processRunId, action } = processLog;
    console.log('event: ', JSON.stringify(event));
    console.log('--- processRunId', processRunId);
    console.log('--- action', action);
    await db_1.createOrGetDBConnection();
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_1.UsersProcessesRepository);
    const userProcess = await usersProcessesRepository.getByProcessRunId(processRunId);
    if (!userProcess) {
        return callback(null);
    }
    const credentials = userProcess.process.credentials;
    if (action === robocloud_action_1.ROBOCLOUD_ACTION.START && userProcess.status !== users_processes_1.PROCESS_STATUS.PROCESSING) {
        userProcess.setStatus(users_processes_1.PROCESS_STATUS.PROCESSING);
        userProcess.setStartTime(new Date().toISOString());
        const { runNo } = await robocorp_1.monitorRobocorp({
            processRunId,
            ...credentials,
        });
        if (!userProcess.robocorpId) {
            userProcess.setRobocorpRunId(runNo);
        }
    }
    else if (action === robocloud_action_1.ROBOCLOUD_ACTION.END && userProcess.status !== users_processes_1.PROCESS_STATUS.FINISHED) {
        const { state, result, workItemStats, robotRuns } = await robocorp_1.monitorRobocorp({
            processRunId,
            ...credentials,
        });
        console.log(`state: ${state}, result: ${result}, robotRuns: ${robotRuns}, workItemStats: ${JSON.stringify(workItemStats)}`);
        if (state === 'COMPL' || state === 'PENDING') {
            if (userProcess.status !== users_processes_1.PROCESS_STATUS.WARNING) {
                switch (result) {
                    case 'OK':
                        if (workItemStats.failedCount === 0) {
                            userProcess.setStatus(users_processes_1.PROCESS_STATUS.FINISHED);
                        }
                        else {
                            userProcess.setStatus(users_processes_1.PROCESS_STATUS.FAILED);
                        }
                        break;
                    case 'ERR':
                    case 'TERMINATED':
                    case 'TIMEOUT':
                        userProcess.setStatus(users_processes_1.PROCESS_STATUS.FAILED);
                        break;
                    default:
                        userProcess.setStatus(users_processes_1.PROCESS_STATUS.FAILED);
                        break;
                }
            }
            const { id: robotRunsId } = robotRuns[0];
            await processArtifacts_1.processArtifacts(userProcess, robotRunsId);
            userProcess.setEndTime(new Date().toISOString());
            userProcess.setDuration();
        }
    }
    await usersProcessesRepository.update(userProcess);
};
exports.handler = middy_1.default(rawHandler).use(middlewares_1.doNotWaitForEmptyEventLoop()).use(sqs_body_parse_1.sqsBodyParse());
//# sourceMappingURL=index.js.map