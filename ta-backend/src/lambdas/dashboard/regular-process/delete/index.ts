import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { createOrGetDBConnection } from '@/utils/db';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { IDeleteRegularProcessPathParams, IDeleteRegularProcessResponse } from './types';
import {RegularProcessRepository} from "@/repositories/RegularProcess";
import AWS from 'aws-sdk';


const eventBridge = new AWS.EventBridge();
const lambda = new AWS.Lambda();

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  {}, IDeleteRegularProcessResponse, IDeleteRegularProcessPathParams
> = async (event) => {
  console.log('Event: ', event);
  const { id } = event.pathParameters;

  await createOrGetDBConnection();

  const regularProcessRepository = getCustomRepository(RegularProcessRepository);

  await regularProcessRepository.delete(id);

  const ruleName = `RegularProcess${id}`;

  await eventBridge.removeTargets({
    Rule: ruleName,
    Ids: [`${ruleName}-target`],
    Force: true,
  }).promise();

  const permissionParams = {
      FunctionName: global.process.env.START_PROCESS_LAMBDA_ARN!,
      StatementId: ruleName,
  };
  await lambda.removePermission(permissionParams).promise();

  await eventBridge.deleteRule({
    Name: ruleName,
    Force: true,
  }).promise();

  return {
    statusCode: 200,
    body: {},
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
