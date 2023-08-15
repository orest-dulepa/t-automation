import { CloudFormationCustomResourceEvent } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop } from 'middy/middlewares';

import cfnCustomResourceWrapper, { Response } from '@/middlewares/cfn-custom-resource-wrapper';

import { createOrGetDBConnection } from '@/utils/db';

import migrations from '@/migrations';

interface OfflineEvent {
  isOffline: boolean;
  isRevert: boolean;
}

function isCFNEvent(event: object): event is CloudFormationCustomResourceEvent {
  return Object.prototype.hasOwnProperty.call(event, 'ServiceToken');
}

async function rawHandler(
  event: CloudFormationCustomResourceEvent | OfflineEvent,
): Promise<Response> {
  if (!isCFNEvent(event) || event.RequestType !== 'Delete') {
    const connection = await createOrGetDBConnection();

    if (isCFNEvent(event) || !event.isRevert) {
      console.log('Running migrations...');

      await connection.runMigrations();

      console.log('Migrations completed!');
    } else {
      console.log(`Reverting ${migrations.length} migration(s)...`);

      for (const ignoredMigration of migrations) {
        await connection.undoLastMigration();
      }

      console.log('Revert completed!');
    }
  }

  return {
    status: 'SUCCESS',
  };
}

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(cfnCustomResourceWrapper());
