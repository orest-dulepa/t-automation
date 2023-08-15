import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { OrganizationRepository } from '@/repositories/Organization';

import { Organization } from '@/entities/Organization';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IOrganizationCreateRequest, IOrganizationCreateResponse } from './types';
import { organizationCreateSchema } from './schema';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IOrganizationCreateRequest,
  IOrganizationCreateResponse
> = async (event) => {
  await createOrGetDBConnection();

  const organizationRepository = getCustomRepository(OrganizationRepository);

  const { name } = event.body;

  const organization = await organizationRepository.insert(new Organization(name));

  return {
    statusCode: 200,
    body: {
      id: Number(organization.id),
      name: organization.name,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(organizationCreateSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
