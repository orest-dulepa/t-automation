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
const Process_1 = require("@/repositories/Process");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const processRepository = typeorm_1.getCustomRepository(Process_1.ProcessRepository);
    const { id } = event.pathParameters;
    const { affected } = await processRepository.delete(id);
    return {
        statusCode: 200,
        body: {
            affected,
        },
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map