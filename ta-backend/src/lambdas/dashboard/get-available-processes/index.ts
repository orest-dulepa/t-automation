import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { badRequest } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { OrganizationsToProcessesRepository } from '@/repositories/OrganizationsToProcesses';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';

import { IGetAvailableProcesses } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<{}, IGetAvailableProcesses> = async (
  event,
) => {
  await createOrGetDBConnection();

  const organizationsToProcessesRepository = getCustomRepository(OrganizationsToProcessesRepository);

  const { authorizer: user } = event.requestContext;
  const { organization } = user;

  if (!organization) throw badRequest("user doesn't have organization");

  const organizationsToProcesses = await organizationsToProcessesRepository.getByOrganizationId(organization.id);

  const mappedProcesses = organizationsToProcesses.map(({ process }) => {
    const { id, name, type, properties } = process;

    return {
      id,
      name,
      type,
      properties,
    };
  });

  return {
    statusCode: 200,
    body: mappedProcesses,
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(authParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
