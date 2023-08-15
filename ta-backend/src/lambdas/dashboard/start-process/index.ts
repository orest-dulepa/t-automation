import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import AWS from 'aws-sdk';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';
import { IProcessStartRequest, IProcessStartPathParams, IProcessStartResponse } from './types';
import {PROPERTY_TYPE} from '@/@types/process';

const lambda = new AWS.Lambda();

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IProcessStartRequest,
  IProcessStartResponse | {},
  IProcessStartPathParams
> = async (event) => {
  console.log('Event: ', event);
  const { body, pathParameters, requestContext } = event;
  const { id } = pathParameters;
  const { authorizer: user } = requestContext;

  const changeStatusUrl = `https://${event.requestContext.domainName}/${event.requestContext.stage}/processes/change-status`;
  const dataForBot = [
    { name: 'Change Status Url', api_name: 'changeStatusUrl', value: changeStatusUrl, type: PROPERTY_TYPE.text },
  ];

  const lambdaParams = {
    FunctionName: process.env.START_PROCESS_LAMBDA_ARN!,
    InvocationType: 'RequestResponse',
    Payload: JSON.stringify({
      processId: id,
      userId: user.id,
      meta: body || [],
      dataForBot: dataForBot || [],
      changeStatusUrl,
    }),
  };

  await lambda
    .invoke(lambdaParams)
    .promise()
    .catch((e) => console.log(e));

  return {
    statusCode: 201,
    body: {},
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(authParser())
  .use(jsonBodyParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
