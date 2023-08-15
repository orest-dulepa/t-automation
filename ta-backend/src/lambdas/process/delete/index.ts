import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';

import { ProcessRepository } from '@/repositories/Process';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IProcessDeletePathParams, IProcessDeleteResponse } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {},
  IProcessDeleteResponse,
  IProcessDeletePathParams
> = async (event) => {
  await createOrGetDBConnection();

  const processRepository = getCustomRepository(ProcessRepository);

  const { id } = event.pathParameters;

  const { affected } = await processRepository.delete(id);

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
