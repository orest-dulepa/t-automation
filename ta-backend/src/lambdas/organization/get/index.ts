import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { notFound } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { OrganizationRepository } from '@/repositories/Organization';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IOrganizationGetPathParams, IOrganizationGetResponse } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {},
  IOrganizationGetResponse,
  IOrganizationGetPathParams
> = async (event) => {
  await createOrGetDBConnection();

  const organizationRepository = getCustomRepository(OrganizationRepository);

  const { id } = event.pathParameters;

  const organization = await organizationRepository.getById(id);

  if (!organization) throw notFound('organization was not found');

  return {
    statusCode: 200,
    body: organization,
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
