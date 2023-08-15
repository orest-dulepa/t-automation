"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const boom_1 = require("@hapi/boom");
const typeorm_1 = require("typeorm");
const db_1 = require("@/utils/db");
const OrganizationsToProcesses_1 = require("@/repositories/OrganizationsToProcesses");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const auth_parser_1 = require("@/middlewares/auth-parser");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const organizationsToProcessesRepository = typeorm_1.getCustomRepository(OrganizationsToProcesses_1.OrganizationsToProcessesRepository);
    const { authorizer: user } = event.requestContext;
    const { organization } = user;
    if (!organization)
        throw boom_1.badRequest("user doesn't have organization");
    const organizationsToProcesses = await organizationsToProcessesRepository.getByOrganizationId(organization.id);
    const mappedProcesses = organizationsToProcesses.map(({ process }) => {
        const { id, name, type, properties } = process;
        return {
            id,
            name,
            type,
            properties,
        };
    });
    return {
        statusCode: 200,
        body: mappedProcesses,
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(auth_parser_1.authParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map