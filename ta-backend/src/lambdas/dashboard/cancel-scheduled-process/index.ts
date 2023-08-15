import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { notFound } from '@hapi/boom';

import { createOrGetDBConnection } from '@/utils/db';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';

import { ScheduledProcessesRepository } from '@/repositories/ScheduledProcesses';

import { SCHEDULED_PROCESS_STATUS } from '@/@types/scheduled-processes';

import { ICancelScheduledProcessPathParams, ICancelScheduledProcessResponse } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {},
  ICancelScheduledProcessResponse,
  ICancelScheduledProcessPathParams
> = async (event) => {
  await createOrGetDBConnection();

  const scheduledProcessesRepository = getCustomRepository(ScheduledProcessesRepository);

  const { id } = event.pathParameters;

  const scheduledProcess = await scheduledProcessesRepository.getById(id);

  if (!scheduledProcess) notFound(`scheduled process ${id} was not found`);

  await scheduledProcessesRepository.updateStatusById(id, SCHEDULED_PROCESS_STATUS.CANCELED);

  return {
    statusCode: 201,
    body: {},
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(authParser())
  .use(jsonBodyParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
