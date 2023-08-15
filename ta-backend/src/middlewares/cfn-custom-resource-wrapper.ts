import { CloudFormationCustomResourceEvent, Context } from 'aws-lambda';
import { MiddlewareObject } from 'middy';
import axios from 'axios';

import { sleep } from '@/utils/sleep';

export interface Response {
  status: 'SUCCESS' | 'FAILED';
  reason?: string;
  data?: object;
}

function isCFNEvent(event: object): event is CloudFormationCustomResourceEvent {
  return 'LogicalResourceId' in event;
}

async function sendResponse({
  event,
  context,
  response,
}: {
  event: CloudFormationCustomResourceEvent;
  context: Context;
  response: Response;
}) {
  const payload = {
    Status: response.status,
    Reason: response.reason,
    PhysicalResourceId: context.logGroupName || event.LogicalResourceId,
    LogicalResourceId: event.LogicalResourceId,
    StackId: event.StackId,
    RequestId: event.RequestId,
    Data: response.data,
  };

  console.log(`Payload: ${JSON.stringify(payload, undefined, 2)}`);

  console.log(`PUTting payload to ${event.ResponseURL}`);

  for (let i = 0; i < 5; i++) {
    try {
      await axios.put(event.ResponseURL, JSON.stringify(payload));

      return;
    } catch (e) {
      console.log('ERROR PUT', e);

      if (i < 4) {
        await sleep(1000);
      }
    }
  }
}

export default function cfnCustomResourceWrapper(): MiddlewareObject<object, Response> {
  return {
    after: async (handler) => {
      if (isCFNEvent(handler.event)) {
        await sendResponse({
          event: handler.event,
          response: handler.response,
          context: handler.context,
        });
      }
    },
    onError: async (handler) => {
      console.error('onError:', handler.error);

      if (isCFNEvent(handler.event)) {
        await sendResponse({
          event: handler.event,
          response: {
            status: 'FAILED',
            reason: handler.error.message,
          },
          context: handler.context,
        });
      }
    },
  };
}
