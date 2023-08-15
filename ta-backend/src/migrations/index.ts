// Imports all the migrations from 'src/migrations' folder and re-exports them as a list

import RequireContext = __WebpackModuleApi.RequireContext;

interface Class {
  new (...args: any[]): any;
}

let requireMigration: RequireContext | undefined;
try {
  // Migration file names follow the format '<timestamp>-<name>.ts'
  requireMigration = require.context('./', true, /^\.\/[0-9]+-.*\.ts$/i);
} catch (e) {
  console.error(e);
}

const migrations: Class[] = [];
if (requireMigration) {
  for (const key of requireMigration.keys()) {
    migrations.push(Object.values(requireMigration(key) as { [className: string]: Class })[0]);
  }
}

export default migrations;
