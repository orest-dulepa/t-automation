import { Handler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { createOrGetDBConnection } from '@/utils/db';
import { UsersProcessesRepository } from '@/repositories/UsersProcesses';
import {IProcessLogsRobocloudMonitorOneEvent} from "./types";
import {IRobocorpCredential} from "@/@types/process";
import {monitorRobocorp} from "@/http-clients/robocorp";
import {processLogs} from "@/utils/processLogs";

const rawHandler: Handler<IProcessLogsRobocloudMonitorOneEvent> = async (event, context, callback) => {
  const { processId } = event;

  await createOrGetDBConnection();

  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);

  const userProcess = await usersProcessesRepository.getById(processId);
  if (!userProcess) return callback(null);

  const processRunId = userProcess.processRunId;
  const credentials = userProcess.process.credentials as IRobocorpCredential;
  const { robotRuns } = await monitorRobocorp({
    processRunId,
    ...credentials,
  });
  const {id: robotRunsId} = robotRuns[0];

  await processLogs(userProcess, robotRunsId);

  return callback(null);
};

export const handler = middy(rawHandler).use(doNotWaitForEmptyEventLoop());
