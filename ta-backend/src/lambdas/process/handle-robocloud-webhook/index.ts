import { APIGatewayProxyHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { createOrGetDBConnection } from '@/utils/db';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { UsersProcessesRepository } from '@/repositories/UsersProcesses';
import { EventRepository } from '@/repositories/Event';
import ProcessRunEventHandler from './events-handlers/ProcessRunEventHandler';
import RobotRunEventHandler from './events-handlers/RobotRunEventHandler';
import { IProcessRobocloudWebhookRequest } from './types';
import AWS from "aws-sdk";

const sqs = new AWS.SQS();

const rawHandler: APIGatewayProxyHandler<IProcessRobocloudWebhookRequest> = async (event) => {
  console.log('Event', event);
  const { body } = event;


  const stringifyChunk = JSON.stringify({
    processRunId: body.payload.processRunId,
    action: body.action,
  });
  const params = {
    MessageBody: stringifyChunk,
    QueueUrl: process.env.PROCESS_HANDLE_QUEUE_ARN!,
    MessageGroupId: body.payload.processRunId,
  };
  await sqs.sendMessage(params).promise();


  await createOrGetDBConnection();

  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);
  const eventRepository = getCustomRepository(EventRepository);

  const handlers = [
    new ProcessRunEventHandler(),
    new RobotRunEventHandler(usersProcessesRepository, eventRepository),
  ];

  const handler = handlers.reduce((a, b) => {
    b.setNext(a);
    return b;
  });

  await handler.try(body).catch((e) => {
    console.log(e);
  });

  return {
    statusCode: 200,
    body: {},
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
