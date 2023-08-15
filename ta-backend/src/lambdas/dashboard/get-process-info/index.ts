import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import AWS from 'aws-sdk';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { notFound, forbidden } from '@hapi/boom';

import { createOrGetDBConnection } from '@/utils/db';

import { PROCESS_STATUS } from '@/@types/users-processes';
import { ROLE } from '@/@types/role';

import { UsersProcessesRepository } from '@/repositories/UsersProcesses';
import { EventRepository } from '@/repositories/Event';
import { LogRepository } from '@/repositories/Log';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';
import { IUsersProcessesGetPathParams, IUsersProcessesGetResponse } from './types';

const s3 = new AWS.S3();

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {},
  IUsersProcessesGetResponse,
  IUsersProcessesGetPathParams
> = async (event) => {
  await createOrGetDBConnection();

  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);
  const eventRepository = getCustomRepository(EventRepository);
  const logRepository = getCustomRepository(LogRepository);

  const { id: processId } = event.pathParameters;
  const { authorizer: user } = event.requestContext;
  const { id: userId, organization, role } = user;
  const { id: organizationId, name: organizationName } = organization;
  const { id: roleId } = role;

  const isManager = roleId === ROLE.MANAGER;
  const isAdmin = (roleId === ROLE.ADMIN && organizationName === 'ta');

  const userProcess = await usersProcessesRepository.getById(processId);

  if (!userProcess) throw notFound('process wasn\'t found');

  const isUserProcessOwner = Number(userId) === Number(userProcess.user.id);
  const isOrganizationProcessOwner = Number(organizationId) === Number(userProcess.organization.id);

  if (!isAdmin && !isOrganizationProcessOwner) throw forbidden('process doesn\'t belong to user organization');
  if (!isAdmin && !isManager && !isUserProcessOwner) throw forbidden('process doesn\'t belong to user');

  const { Contents } = await s3
    .listObjectsV2({
      Bucket: process.env.BUCKET_NAME,
      Prefix: userProcess.processRunId,
      FetchOwner: false,
    })
    .promise();

  const artifacts = Contents?.map(({ Key: key, Size: size }) => ({ key, size })) || [];

  const events = await eventRepository.getAllByUserProcessId(userProcess.id);
  const log = await logRepository.getByUserProcessId(userProcess.id);

  const mappedEvents = events.map(({ seqNo, eventType, timeStamp }) => ({
    seqNo,
    eventType,
    timeStamp,
  }));

  if (events.length === 0) {
    mappedEvents.push({
      seqNo: '1',
      eventType: 'TA Logger event: Starting',
      timeStamp: userProcess.startTime || '',
    });
  }

  if (mappedEvents.length === 1 && userProcess.endTime) {
    const finalEvent = { seqNo: '2', eventType: '', timeStamp: '' };

    if (userProcess.status === PROCESS_STATUS.FAILED) {
      finalEvent.eventType = 'TA Logger event: Failed';
    }

    if (userProcess.status === PROCESS_STATUS.FINISHED) {
      finalEvent.eventType = 'TA Logger event: Finishing';
    }

    finalEvent.timeStamp = userProcess.endTime;

    mappedEvents.push(finalEvent);
  }

  return {
    statusCode: 200,
    body: {
      ...userProcess,
      artifacts,
      logs: log?.text || '',
      events: mappedEvents,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(authParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
