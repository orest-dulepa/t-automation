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
const Process_1 = require("@/repositories/Process");
const User_1 = require("@/repositories/User");
const OrganizationsToProcesses_1 = require("@/repositories/OrganizationsToProcesses");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const auth_parser_1 = require("@/middlewares/auth-parser");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const processRepository = typeorm_1.getCustomRepository(Process_1.ProcessRepository);
    const userRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
    const organizationsToProcessesRepository = typeorm_1.getCustomRepository(OrganizationsToProcesses_1.OrganizationsToProcessesRepository);
    const { requestContext } = event;
    const { authorizer: user } = requestContext;
    const { id: userId, organization, role } = user;
    const { id: organizationId, name: organizationName } = organization;
    const { id: roleId } = role;
    const isManager = roleId === role_1.ROLE.MANAGER;
    const isAdmin = roleId === role_1.ROLE.ADMIN && organizationName === 'ta';
    let processes;
    let users;
    switch (true) {
        case isAdmin: {
            processes = await processRepository.getAll();
            users = await userRepository.getAll();
            break;
        }
        case isManager: {
            const organizationsToProcesses = await organizationsToProcessesRepository.getByOrganizationId(organizationId);
            processes = organizationsToProcesses.map(({ process }) => process);
            users = await userRepository.getAllByOrganizationId(organizationId);
            break;
        }
        default: {
            const organizationsToProcesses = await organizationsToProcessesRepository.getByOrganizationId(organizationId);
            processes = organizationsToProcesses.map(({ process }) => process);
            const user = await userRepository.getById(userId);
            users = [user];
        }
    }
    return {
        statusCode: 200,
        body: {
            processes,
            users,
        },
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(auth_parser_1.authParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map