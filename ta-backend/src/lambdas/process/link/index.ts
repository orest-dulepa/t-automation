import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { badRequest } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { ProcessRepository } from '@/repositories/Process';
import { OrganizationRepository } from '@/repositories/Organization';
import { OrganizationsToProcessesRepository } from '@/repositories/OrganizationsToProcesses';

import { OrganizationsToProcesses } from '@/entities/OrganizationsToProcesses';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IProcessLinkRequest, IProcessLinkResponse } from './types';
import { processLinkSchema } from './schema';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IProcessLinkRequest,
  IProcessLinkResponse
> = async (event) => {
  await createOrGetDBConnection();

  const processRepository = getCustomRepository(ProcessRepository);
  const organizationRepository = getCustomRepository(OrganizationRepository);
  const organizationsToProcessesRepository = getCustomRepository(OrganizationsToProcessesRepository);

  const { organizationId, processId } = event.body;

  const organization = await organizationRepository.getById(organizationId);

  if (!organization) throw badRequest('organizationId is invalid');

  const process = await processRepository.getById(processId);

  if (!process) throw badRequest('processId is invalid');

  const organizationsToProcesses = new OrganizationsToProcesses(organization, process);

  await organizationsToProcessesRepository.insert(organizationsToProcesses);

  return {
    statusCode: 200,
    body: organizationsToProcesses,
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(processLinkSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
