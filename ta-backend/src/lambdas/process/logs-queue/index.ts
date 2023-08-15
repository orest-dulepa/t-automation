// Example of usage:

// const stringifyChunk = JSON.stringify({ processRunId: 'aa82a6e2-0ef0-499f-899d-d2bb89d26cd8', message: 'TEST' });
//
// const params = {
//   MessageBody: stringifyChunk,
//   QueueUrl: String(global.process.env.LOGS_QUEUE_URL)
// };
// sqs.sendMessage(params, () => {});

import { SQSHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { createOrGetDBConnection } from '@/utils/db';
import { UsersProcessesRepository } from '@/repositories/UsersProcesses';
import { LogRepository } from '@/repositories/Log';
import { sqsBodyParse } from '@/middlewares/sqs-body-parse';
import { IProcessLogQueue } from "@/lambdas/process/logs-queue/types";
import { Log } from "@/entities/Log";


const rawHandler: SQSHandler<IProcessLogQueue> = async (event, context, callback) => {
  const { Records } = event;
  const [{ body: processLog}] = Records;
  const { processRunId, message } = processLog;

  console.log('--- processRunId', processRunId);
  console.log('--- message', message);
  console.log('event: ', JSON.stringify(event));

  await createOrGetDBConnection();

  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);
  const logsRepository = getCustomRepository(LogRepository);

  const userProcess = await usersProcessesRepository.getByProcessRunId(processRunId);
  if (!userProcess) return callback(null);

  let log = await logsRepository.getByUserProcessId(userProcess.id);

  if (!log) {
    log = new Log(message, userProcess);
  } else {
    log.text = `${log.text}\n${message}`;
  }

  await logsRepository.update(log);

  return callback(null);
};

export const handler = middy(rawHandler).use(doNotWaitForEmptyEventLoop()).use(sqsBodyParse());
