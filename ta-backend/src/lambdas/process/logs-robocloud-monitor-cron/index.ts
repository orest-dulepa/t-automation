import { ScheduledHandler } from 'aws-lambda';
import AWS from 'aws-sdk';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop } from 'middy/middlewares';
import { sleep } from '@/utils/sleep';

const lambda = new AWS.Lambda();

const rawHandler: ScheduledHandler = async (event, context, callback) => {
  let INVOCATION_COUNT = 0;

  while (true) {
    console.log('INVOCATION_COUNT', INVOCATION_COUNT);

    if (INVOCATION_COUNT >= 23) {
      return callback(null);
    }

    const lambdaParams = {
      FunctionName: process.env.LOGS_ROBOCLOUD_MONITOR_ALL_LAMBDA_ARN!,
      InvocationType: 'Event',
    };

    lambda.invoke(lambdaParams).promise().catch((e) => console.log(e));

    INVOCATION_COUNT++;

    await sleep(2500);
  }
};

export const handler = middy(rawHandler).use(doNotWaitForEmptyEventLoop());
