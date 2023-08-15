"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.processLogs = void 0;
const typeorm_1 = require("typeorm");
const Log_1 = require("@/repositories/Log");
const robocorp_1 = require("@/http-clients/robocorp");
exports.processLogs = async (userProcess, robotRunsId) => {
    const credentials = userProcess.process.credentials;
    const processRunId = userProcess.processRunId;
    const logRepository = typeorm_1.getCustomRepository(Log_1.LogRepository);
    const logs = await robocorp_1.requestWithRetry({ func: robocorp_1.getRobocorpLogs, args: { processRunId, ...credentials, robotRunsId } });
    if (logs) {
        const logText = logs.sort((a, b) => a.seqNo - b.seqNo).reduce((a, b) => a + b.message, '');
        await logRepository.upsert(logText, userProcess);
    }
};
//# sourceMappingURL=processLogs.js.map