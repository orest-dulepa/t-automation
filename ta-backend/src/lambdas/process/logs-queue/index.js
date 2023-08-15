"use strict";
// Example of usage:
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
const Log_1 = require("@/repositories/Log");
const sqs_body_parse_1 = require("@/middlewares/sqs-body-parse");
const Log_2 = require("@/entities/Log");
const rawHandler = async (event, context, callback) => {
    const { Records } = event;
    const [{ body: processLog }] = Records;
    const { processRunId, message } = processLog;
    console.log('--- processRunId', processRunId);
    console.log('--- message', message);
    console.log('event: ', JSON.stringify(event));
    await db_1.createOrGetDBConnection();
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_1.UsersProcessesRepository);
    const logsRepository = typeorm_1.getCustomRepository(Log_1.LogRepository);
    const userProcess = await usersProcessesRepository.getByProcessRunId(processRunId);
    if (!userProcess)
        return callback(null);
    let log = await logsRepository.getByUserProcessId(userProcess.id);
    if (!log) {
        log = new Log_2.Log(message, userProcess);
    }
    else {
        log.text = `${log.text}\n${message}`;
    }
    await logsRepository.update(log);
    return callback(null);
};
exports.handler = middy_1.default(rawHandler).use(middlewares_1.doNotWaitForEmptyEventLoop()).use(sqs_body_parse_1.sqsBodyParse());
//# sourceMappingURL=index.js.map