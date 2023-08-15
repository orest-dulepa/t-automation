"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const cfn_custom_resource_wrapper_1 = __importDefault(require("@/middlewares/cfn-custom-resource-wrapper"));
const db_1 = require("@/utils/db");
const migrations_1 = __importDefault(require("@/migrations"));
function isCFNEvent(event) {
    return Object.prototype.hasOwnProperty.call(event, 'ServiceToken');
}
async function rawHandler(event) {
    if (!isCFNEvent(event) || event.RequestType !== 'Delete') {
        const connection = await db_1.createOrGetDBConnection();
        if (isCFNEvent(event) || !event.isRevert) {
            console.log('Running migrations...');
            await connection.runMigrations();
            console.log('Migrations completed!');
        }
        else {
            console.log(`Reverting ${migrations_1.default.length} migration(s)...`);
            for (const ignoredMigration of migrations_1.default) {
                await connection.undoLastMigration();
            }
            console.log('Revert completed!');
        }
    }
    return {
        status: 'SUCCESS',
    };
}
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(cfn_custom_resource_wrapper_1.default());
//# sourceMappingURL=index.js.map