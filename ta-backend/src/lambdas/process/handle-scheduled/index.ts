import { Handler } from 'aws-lambda';
import AWS from 'aws-sdk';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { SCHEDULED_PROCESS_STATUS } from '@/@types/scheduled-processes';

import { ScheduledProcessesRepository } from '@/repositories/ScheduledProcesses';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IHandleScheduledProcessRequest } from './types';

import {PROPERTY_TYPE} from "@/@types/process";

const lambda = new AWS.Lambda();

const rawHandler: Handler<IHandleScheduledProcessRequest> = async (event) => {
  await createOrGetDBConnection();

  const scheduledProcessesRepository = getCustomRepository(ScheduledProcessesRepository);

  console.log('scheduledEvent', event);

  const { scheduledProcessId, changeStatusUrl } = event.Payload.Input;

  const scheduledProcess = await scheduledProcessesRepository.getById(scheduledProcessId);

  if (!scheduledProcess) return;

  if (scheduledProcess.status === SCHEDULED_PROCESS_STATUS.CANCELED) return;

  const dataForBot = [
    { name: 'Change Status Url', api_name: 'changeStatusUrl', value: changeStatusUrl, type: PROPERTY_TYPE.text },
  ];

  const lambdaParams = {
    FunctionName: process.env.START_PROCESS_LAMBDA_ARN!,
    InvocationType: 'RequestResponse',
    Payload: JSON.stringify({
      processId: scheduledProcess.process.id,
      userId: scheduledProcess.user.id,
      meta: scheduledProcess.meta || [],
      dataForBot: dataForBot || [],
    }),
  };

  await lambda
    .invoke(lambdaParams)
    .promise()
    .catch((e) => console.log(e));

  await scheduledProcessesRepository.updateStatusById(scheduledProcessId, SCHEDULED_PROCESS_STATUS.SUCCEEDED);
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(errorHandler())
  .use(jsonBodySerializer());
