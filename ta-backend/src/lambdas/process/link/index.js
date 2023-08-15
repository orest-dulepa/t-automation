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
const Process_1 = require("@/repositories/Process");
const Organization_1 = require("@/repositories/Organization");
const OrganizationsToProcesses_1 = require("@/repositories/OrganizationsToProcesses");
const OrganizationsToProcesses_2 = require("@/entities/OrganizationsToProcesses");
const validator_1 = require("@/middlewares/validator");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const schema_1 = require("./schema");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const processRepository = typeorm_1.getCustomRepository(Process_1.ProcessRepository);
    const organizationRepository = typeorm_1.getCustomRepository(Organization_1.OrganizationRepository);
    const organizationsToProcessesRepository = typeorm_1.getCustomRepository(OrganizationsToProcesses_1.OrganizationsToProcessesRepository);
    const { organizationId, processId } = event.body;
    const organization = await organizationRepository.getById(organizationId);
    if (!organization)
        throw boom_1.badRequest('organizationId is invalid');
    const process = await processRepository.getById(processId);
    if (!process)
        throw boom_1.badRequest('processId is invalid');
    const organizationsToProcesses = new OrganizationsToProcesses_2.OrganizationsToProcesses(organization, process);
    await organizationsToProcessesRepository.insert(organizationsToProcesses);
    return {
        statusCode: 200,
        body: organizationsToProcesses,
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(validator_1.validator(schema_1.processLinkSchema))
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map