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
const Organization_1 = require("@/repositories/Organization");
const Organization_2 = require("@/entities/Organization");
const validator_1 = require("@/middlewares/validator");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const schema_1 = require("./schema");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const organizationRepository = typeorm_1.getCustomRepository(Organization_1.OrganizationRepository);
    const { name } = event.body;
    const organization = await organizationRepository.insert(new Organization_2.Organization(name));
    return {
        statusCode: 200,
        body: {
            id: Number(organization.id),
            name: organization.name,
        },
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(validator_1.validator(schema_1.organizationCreateSchema))
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map