import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { notFound } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { ProcessRepository } from '@/repositories/Process';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IProcessGetResponse, IProcessGetPathParams } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {},
  IProcessGetResponse,
  IProcessGetPathParams
> = async (event) => {
  await createOrGetDBConnection();

  const processRepository = getCustomRepository(ProcessRepository);

  const { id } = event.pathParameters;

  const process = await processRepository.getById(id);

  if (!process) throw notFound('process was not found');

  return {
    statusCode: 200,
    body: {
      id: Number(process.id),
      name: process.name,
      type: process.type,
      properties: process.properties,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
