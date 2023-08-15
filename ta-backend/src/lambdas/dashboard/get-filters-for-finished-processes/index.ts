import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { ROLE } from '@/@types/role';

import { Process } from '@/entities/Process';
import { User } from '@/entities/User';

import { ProcessRepository } from '@/repositories/Process';
import { UserRepository } from '@/repositories/User';
import { OrganizationsToProcessesRepository } from '@/repositories/OrganizationsToProcesses';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';

import { IGetFiltersForFinishedProcesses } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {},
  IGetFiltersForFinishedProcesses
> = async (event) => {
  await createOrGetDBConnection();

  const processRepository = getCustomRepository(ProcessRepository);
  const userRepository = getCustomRepository(UserRepository);
  const organizationsToProcessesRepository = getCustomRepository(
    OrganizationsToProcessesRepository,
  );

  const { requestContext } = event;
  const { authorizer: user } = requestContext;
  const { id: userId, organization, role } = user;
  const { id: organizationId, name: organizationName } = organization;
  const { id: roleId } = role;

  const isManager = roleId === ROLE.MANAGER;
  const isAdmin = roleId === ROLE.ADMIN && organizationName === 'ta';

  let processes: Process[];
  let users: User[];

  switch (true) {
      case isAdmin: {
        processes = await processRepository.getAll();
        users = await userRepository.getAll();
        break;
      }
      case isManager: {
        const organizationsToProcesses = await organizationsToProcessesRepository.getByOrganizationId(organizationId);
        processes = organizationsToProcesses.map(({ process }) => process);
        users = await userRepository.getAllByOrganizationId(organizationId);
        break;
      }
      default: {
        const organizationsToProcesses = await organizationsToProcessesRepository.getByOrganizationId(organizationId);
        processes = organizationsToProcesses.map(({ process }) => process);

        const user = await userRepository.getById(userId);
        users = [user!];
      }
  }

  return {
    statusCode: 200,
    body: {
      processes,
      users,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(authParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
