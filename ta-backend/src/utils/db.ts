import once from 'lodash/once';
import { PostgresConnectionOptions } from 'typeorm/driver/postgres/PostgresConnectionOptions';
import { getConnection, getConnectionManager, createConnection } from 'typeorm';

export const createOrGetDBConnection = once(
  async (options: Partial<PostgresConnectionOptions> = {}) => {
    const ormconfig = await import('../../ormconfig');

    if (getConnectionManager().has('default')) {
      return getConnection();
      // await getConnection().close();
    }

    return createConnection({
      ...ormconfig,
      ...options,
    });
  },
);
