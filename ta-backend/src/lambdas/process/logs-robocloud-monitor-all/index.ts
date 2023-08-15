import { ScheduledHandler } from 'aws-lambda';
import AWS from 'aws-sdk';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { createOrGetDBConnection } from '@/utils/db';
import { UsersProcessesRepository } from '@/repositories/UsersProcesses';

const lambda = new AWS.Lambda();

const rawHandler: ScheduledHandler = async (event, context, callback) => {
  await createOrGetDBConnection();

  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);

  const processingProcesses = await usersProcessesRepository.getProcessing();
  console.log('processingProcesses: ', processingProcesses);

  for (const processingProcess of processingProcesses) {
    const lambdaParams = {
      FunctionName: process.env.LOGS_ROBOCLOUD_MONITOR_ONE_LAMBDA_ARN!,
      InvocationType: 'Event',
      Payload: JSON.stringify({
        processId: processingProcess.id,
      }),
    };

    lambda.invoke(lambdaParams).promise().catch((e) => console.log(e));
  }

  return callback(null);
};

export const handler = middy(rawHandler).use(doNotWaitForEmptyEventLoop());
