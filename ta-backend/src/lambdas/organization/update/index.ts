import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { notFound } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { OrganizationRepository } from '@/repositories/Organization';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IOrganizationUpdateRequest, IOrganizationUpdateResponse, IOrganizationUpdatePathParams } from './types';
import { organizationUpdateSchema } from './schema';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IOrganizationUpdateRequest,
  IOrganizationUpdateResponse,
  IOrganizationUpdatePathParams
> = async (event) => {
  await createOrGetDBConnection();

  const organizationRepository = getCustomRepository(OrganizationRepository);

  const { id } = event.pathParameters;
  const { name } = event.body;

  const organization = await organizationRepository.getById(id);

  if (!organization) throw notFound('organization was not found');

  if (name) organization.setName(name);

  await organizationRepository.update(organization);

  return {
    statusCode: 200,
    body: organization,
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(organizationUpdateSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
