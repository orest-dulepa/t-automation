import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { ProcessRepository } from '@/repositories/Process';

import { Process } from '@/entities/Process';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IProcessCreateRequest, IProcessCreateResponse } from './types';
import { processCreateSchema } from './schema';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IProcessCreateRequest,
  IProcessCreateResponse
> = async (event) => {
  await createOrGetDBConnection();

  const processRepository = getCustomRepository(ProcessRepository);

  const { name, type, credentials, properties } = event.body;

  const process = await processRepository.insert(new Process(name, type, credentials, properties));

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
  .use(jsonBodyParser())
  .use(validator(processCreateSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
