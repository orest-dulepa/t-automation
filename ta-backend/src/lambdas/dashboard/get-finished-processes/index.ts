import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { ROLE } from '@/@types/role';

import { UsersProcessesRepository } from '@/repositories/UsersProcesses';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';

import { IGetFinishedUserProcesses, IGetFinishedUserProcessesQueryParams } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {},
  IGetFinishedUserProcesses,
  {},
  IGetFinishedUserProcessesQueryParams
> = async (event) => {
  await createOrGetDBConnection();

  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);

  const { queryStringParameters, requestContext } = event;
  const {
    processes_filter,
    statuses_filter,
    inputs_filter,
    end_times_filter,
    executed_by_filter,
    processes_sort,
    run_number_sort,
    duration_sort,
    end_times_sort,
    executed_by_sort,
    amount,
    page,
  } = queryStringParameters || {};
  const { authorizer: user } = requestContext;
  const { id: userId, organization, role } = user;
  const { id: organizationId, name: organizationName } = organization;
  const { id: roleId } = role;

  const isManager = roleId === ROLE.MANAGER;
  const isAdmin = (roleId === ROLE.ADMIN && organizationName === 'ta');

  let organizationIdToSearch: number | undefined;
  let userIdToSearch: number | undefined;
  
  if (isManager) {
    organizationIdToSearch = organizationId;
  }

  if (!isAdmin && !isManager) {
    userIdToSearch = userId;
  }

  const [processes, total] = await usersProcessesRepository.getAllCompleted(
    organizationIdToSearch,
    userIdToSearch,
    processes_filter,
    statuses_filter,
    inputs_filter,
    end_times_filter,
    executed_by_filter,
    processes_sort,
    run_number_sort,
    duration_sort,
    end_times_sort,
    executed_by_sort,
    amount,
    page,
  );

  return {
    statusCode: 200,
    body: {
      processes,
      total,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(authParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
