import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { createOrGetDBConnection } from '@/utils/db';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';
import {
  ICreateRegularProcessRequest,
  ICreateRegularProcessResponse
} from '@/lambdas/dashboard/regular-process/create/types';
import { RegularProcess } from '@/entities/RegularProcess';
import { UserRepository } from '@/repositories/User';
import {badRequest, notFound} from '@hapi/boom';
import { ProcessRepository } from '@/repositories/Process';
import { RegularProcessRepository } from '@/repositories/RegularProcess';
import AWS from 'aws-sdk';
import {PROPERTY_TYPE} from '@/@types/process';


const eventBridge = new AWS.EventBridge();
const lambda = new AWS.Lambda();

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  ICreateRegularProcessRequest,
  ICreateRegularProcessResponse
> = async (event) => {
  console.log('Event: ', event);

  const { body, requestContext } = event;
  const { processId, meta, daysOfWeek, startTime } = body;

  if (daysOfWeek.length === 0) throw badRequest('Time was not set');

  await createOrGetDBConnection();

  const usersRepository = getCustomRepository(UserRepository);
  const processRepository = getCustomRepository(ProcessRepository);
  const regularProcessRepository = getCustomRepository(RegularProcessRepository);

  const user = await usersRepository.getByIdWithOrganizationAndRole(requestContext.authorizer.id);
  if (!user) throw notFound('User was not found');

  const process = await processRepository.getById(processId);
  if (!process) throw notFound('Process was not found');

  const organization = user.organization;
  const regularProcess = new RegularProcess(daysOfWeek, startTime, meta, user, process, organization);
  const regularProcessInstance = await regularProcessRepository.insert(regularProcess);


  const changeStatusUrl = `https://${requestContext.domainName}/${requestContext.stage}/processes/change-status`;
  const dataForBot = [
    { name: 'Change Status Url', api_name: 'changeStatusUrl', value: changeStatusUrl, type: PROPERTY_TYPE.text },
  ];

  const ruleName = `RegularProcess${regularProcessInstance.id}`;
  const [h, m] = startTime.split(':');

  const ruleParams = {
    Name: ruleName,
    ScheduleExpression: `cron(${m} ${h} ? * ${daysOfWeek.join(',')} *)`,
    EventBusName: 'default',
  };
  const rule = await eventBridge.putRule(ruleParams).promise();

  const permissionParams = {
      Action: 'lambda:InvokeFunction',
      FunctionName: global.process.env.START_PROCESS_LAMBDA_ARN!,
      Principal: 'events.amazonaws.com',
      StatementId: ruleName,
      SourceArn: rule.RuleArn,
  };
  await lambda.addPermission(permissionParams).promise();

  const targetParams = {
    Rule: ruleName,
    Targets: [
      {
        Id: `${ruleName}-target`,
        Arn: global.process.env.START_PROCESS_LAMBDA_ARN!,
        Input: JSON.stringify({
          processId,
          userId: user.id,
          meta: meta || [],
          dataForBot: dataForBot || [],
          changeStatusUrl,
        }),
      },
    ],
  };
  await eventBridge.putTargets(targetParams).promise();

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
