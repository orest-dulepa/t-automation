import {UsersProcesses} from "@/entities/UsersProcesses";
import {IRobocorpCredential} from "@/@types/process";
import {getCustomRepository} from "typeorm";
import {LogRepository} from "@/repositories/Log";
import {getRobocorpLogs, requestWithRetry} from "@/http-clients/robocorp";

export const processLogs = async (
  userProcess: UsersProcesses, robotRunsId: string
) => {
  const credentials = userProcess.process.credentials as IRobocorpCredential;
  const processRunId = userProcess.processRunId;

  const logRepository = getCustomRepository(LogRepository);
  const logs = await requestWithRetry({func: getRobocorpLogs, args: {processRunId, ...credentials, robotRunsId}});

  if (logs) {
    const logText = logs.sort((a, b) => a.seqNo - b.seqNo).reduce((a, b) => a + b.message, '');
    await logRepository.upsert(logText, userProcess);
  }
}
