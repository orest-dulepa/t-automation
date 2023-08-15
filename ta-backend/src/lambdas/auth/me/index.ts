import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';

import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';

import { IMeResponse } from './types';

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<{}, IMeResponse> = async (event) => {
  const { authorizer: user } = event.requestContext;
  const { id, firstName, lastName, email, organization, role } = user;

  return {
    statusCode: 200,
    body: {
      id: Number(id),
      email,
      firstName,
      lastName,
      organization,
      role,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(authParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
