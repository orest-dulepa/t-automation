"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const typeorm_1 = require("typeorm");
const db_1 = require("@/utils/db");
const role_1 = require("@/@types/role");
const ScheduledProcesses_1 = require("@/repositories/ScheduledProcesses");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const auth_parser_1 = require("@/middlewares/auth-parser");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const scheduledProcessesRepository = typeorm_1.getCustomRepository(ScheduledProcesses_1.ScheduledProcessesRepository);
    const { authorizer: user } = event.requestContext;
    const { id: userId, organization, role } = user;
    const { id: organizationId, name: organizationName } = organization;
    const { id: roleId } = role;
    const isManager = roleId === role_1.ROLE.MANAGER;
    const isAdmin = (roleId === role_1.ROLE.ADMIN && organizationName === 'ta');
    let organizationIdToSearch;
    let userIdToSearch;
    if (isManager) {
        organizationIdToSearch = organizationId;
    }
    if (!isAdmin && !isManager) {
        userIdToSearch = userId;
    }
    const scheduledProcesses = await scheduledProcessesRepository.getAllScheduled(organizationIdToSearch, userIdToSearch);
    return {
        statusCode: 200,
        body: scheduledProcesses,
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(auth_parser_1.authParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map