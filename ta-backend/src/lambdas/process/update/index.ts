import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { notFound } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { ProcessRepository } from '@/repositories/Process';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IProcessUpdateRequest, IProcessUpdateResponse, IProcessUpdatePathParams } from './types';
import { processUpdateSchema } from './schema';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IProcessUpdateRequest,
  IProcessUpdateResponse,
  IProcessUpdatePathParams
> = async (event) => {
  await createOrGetDBConnection();

  const processRepository = getCustomRepository(ProcessRepository);

  const { id } = event.pathParameters;
  const { name, type, properties } = event.body;

  const process = await processRepository.getById(id);

  if (!process) throw notFound('process was not found');

  if (name) process.setName(name);
  if (type) process.setType(type);
  if (properties) process.setProperties(properties);

  await processRepository.update(process);

  return {
    statusCode: 200,
    body: {
      id: Number(process.id),
      name: process.name,
      properties: process.properties,
      type: process.type,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(processUpdateSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
