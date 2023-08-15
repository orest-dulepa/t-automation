"use strict";
// Imports all the migrations from 'src/migrations' folder and re-exports them as a list
Object.defineProperty(exports, "__esModule", { value: true });
let requireMigration;
try {
    // Migration file names follow the format '<timestamp>-<name>.ts'
    requireMigration = require.context('./', true, /^\.\/[0-9]+-.*\.ts$/i);
}
catch (e) {
    console.error(e);
}
const migrations = [];
if (requireMigration) {
    for (const key of requireMigration.keys()) {
        migrations.push(Object.values(requireMigration(key))[0]);
    }
}
exports.default = migrations;
//# sourceMappingURL=index.js.map