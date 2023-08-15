import { SQSHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop} from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { PROCESS_STATUS } from '@/@types/users-processes';
import { createOrGetDBConnection } from '@/utils/db';
import { UsersProcessesRepository } from '@/repositories/UsersProcesses';
import { IProcessHandler } from "@/lambdas/process/handler-robocloud-queue/types";
import { sqsBodyParse } from "@/middlewares/sqs-body-parse";
import { IRobocorpCredential } from "@/@types/process";
import { monitorRobocorp } from "@/http-clients/robocorp";
import { processArtifacts } from "@/utils/processArtifacts";
import { ROBOCLOUD_ACTION } from "@/@types/robocloud-action";


const rawHandler: SQSHandler<IProcessHandler> = async (event, context, callback) => {
  const { Records } = event;
  const [{ body: processLog}] = Records;
  const { processRunId, action } = processLog;

  console.log('event: ', JSON.stringify(event));
  console.log('--- processRunId', processRunId);
  console.log('--- action', action);

  await createOrGetDBConnection();
  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);
  const userProcess = await usersProcessesRepository.getByProcessRunId(processRunId);

  if (!userProcess) {
    return callback(null);
  }

  const credentials = userProcess.process.credentials as IRobocorpCredential;

  if (action === ROBOCLOUD_ACTION.START && userProcess.status !== PROCESS_STATUS.PROCESSING) {
    userProcess.setStatus(PROCESS_STATUS.PROCESSING);
    userProcess.setStartTime(new Date().toISOString());

    const { runNo } = await monitorRobocorp({
      processRunId,
      ...credentials,
    });

    if (!userProcess.robocorpId) {
      userProcess.setRobocorpRunId(runNo);
    }
  } else if (action === ROBOCLOUD_ACTION.END && userProcess.status !== PROCESS_STATUS.FINISHED) {
    const { state, result, workItemStats, robotRuns } = await monitorRobocorp({
      processRunId,
      ...credentials,
    });
    console.log(`state: ${state}, result: ${result}, robotRuns: ${robotRuns}, workItemStats: ${JSON.stringify(workItemStats)}`);

    if (state === 'COMPL' || state === 'PENDING') {
      if (userProcess.status !== PROCESS_STATUS.WARNING) {
        switch (result) {
          case 'OK':
            if (workItemStats.failedCount === 0) {
              userProcess.setStatus(PROCESS_STATUS.FINISHED);
            } else {
              userProcess.setStatus(PROCESS_STATUS.FAILED);
            }
            break;
          case 'ERR':
          case 'TERMINATED':
          case 'TIMEOUT':
            userProcess.setStatus(PROCESS_STATUS.FAILED);
            break;
          default:
            userProcess.setStatus(PROCESS_STATUS.FAILED);
            break;
        }
      }

      const {id: robotRunsId} = robotRuns[0];
      await processArtifacts(userProcess, robotRunsId);

      userProcess.setEndTime(new Date().toISOString());
      userProcess.setDuration();
    }
  }

  await usersProcessesRepository.update(userProcess);
};

export const handler = middy(rawHandler).use(doNotWaitForEmptyEventLoop()).use(sqsBodyParse());
