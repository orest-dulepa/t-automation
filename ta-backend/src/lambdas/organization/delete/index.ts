import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { OrganizationRepository } from '@/repositories/Organization';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IOrganizationDeleteResponse, IOrganizationDeletePathParams } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {},
  IOrganizationDeleteResponse,
  IOrganizationDeletePathParams
> = async (event) => {
  await createOrGetDBConnection();

  const organizationRepository = getCustomRepository(OrganizationRepository);

  const { id } = event.pathParameters;

  const { affected } = await organizationRepository.delete(id);

  return {
    statusCode: 200,
    body: {
      affected,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
