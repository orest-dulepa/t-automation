import {Handler} from 'aws-lambda';
import middy from 'middy';
import {doNotWaitForEmptyEventLoop} from 'middy/middlewares';
import {notFound} from '@hapi/boom';
import {getCustomRepository} from 'typeorm';
import {createOrGetDBConnection} from '@/utils/db';
import {IProcessChangeStatusAWSEvent} from './types';
import {UsersProcessesRepository} from "@/repositories/UsersProcesses";
import {AWS_PROCESS_STATUS, AWS_PROCESS_STATUS_TO_STANDART_STATUS, PROCESS_STATUS} from "@/@types/users-processes";


const rawHandler: Handler<IProcessChangeStatusAWSEvent> = async (event) => {
  const detailType = event['detail-type'];
  const AWSStatus: AWS_PROCESS_STATUS = event.detail.status;
  const processRunId = JSON.parse(event.detail.input).processRunId;

  console.log('Event: ', event);
  console.log('Type: ', detailType);
  console.log('AWSStatus: ', AWSStatus);
  console.log('ProcessRunId: ', processRunId);

  if (detailType !== 'Step Functions Execution Status Change') return;

  await createOrGetDBConnection();
  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);
  const userProcess = await usersProcessesRepository.getByProcessRunId(processRunId);

  console.log('Before status:', userProcess?.status);
  if (
    userProcess?.status &&
    (userProcess.status !== PROCESS_STATUS.PROCESSING && userProcess.status !== PROCESS_STATUS.INITIALIZED)
  ) return;
  if (!userProcess) throw notFound('UsersProcess was not found');

  const newStatus = AWS_PROCESS_STATUS_TO_STANDART_STATUS[AWSStatus];
  userProcess.setStatus(newStatus);
  console.log(`Set new status ${newStatus} to userProcess ${userProcess.id}`);

  if (AWSStatus !== AWS_PROCESS_STATUS.RUNNING) {
    userProcess.setEndTime(new Date().toISOString());
    userProcess.setDuration();
    console.log(`Set endTime and duration to userProcess ${userProcess.id}`);
  }

  await usersProcessesRepository.update(userProcess);
};

export const handler = middy(rawHandler).use(doNotWaitForEmptyEventLoop());
