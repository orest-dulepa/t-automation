import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import AWS from 'aws-sdk';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { notFound } from '@hapi/boom';
import moment from 'moment';

import { createOrGetDBConnection } from '@/utils/db';

import { ScheduledProcessesRepository } from '@/repositories/ScheduledProcesses';
import { ProcessRepository } from '@/repositories/Process';

import { ScheduledProcess } from '@/entities/ScheduledProcess';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';

import {
  IProcessScheduleRequest,
  IProcessSchedulePathParams,
  IProcessScheduleResponse,
} from './types';

const stepFunctions = new AWS.StepFunctions();

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IProcessScheduleRequest,
  IProcessScheduleResponse | {},
  IProcessSchedulePathParams
> = async (event) => {
  await createOrGetDBConnection();

  const scheduledProcessesRepository = getCustomRepository(ScheduledProcessesRepository);
  const processRepository = getCustomRepository(ProcessRepository);

  const { body, pathParameters, requestContext } = event;
  const { meta, timestamp } = body;
  const { id } = pathParameters;
  const { authorizer: user } = requestContext;

  const processToRun = await processRepository.getById(id);

  if (!processToRun) throw notFound("process wasn't found");

  console.log('timestamp', timestamp);

  const scheduledProcess = await scheduledProcessesRepository.insert(
    new ScheduledProcess(meta, moment(timestamp).valueOf(), user, processToRun, user.organization),
  );

  console.log('scheduledProcess', scheduledProcess);

  const payload = {
    stateMachineArn: process.env.STATE_MACHINE_ARN!,
    input: JSON.stringify({
      timestamp,
      body: {
        scheduledProcessId: scheduledProcess.id,
        changeStatusUrl: `https://${requestContext.domainName}/${requestContext.stage}/processes/change-status`,
      },
    }),
  };

  console.log('payload', payload);

  await stepFunctions
    .startExecution(payload)
    .promise()
    .catch((e) => console.log(e));

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
