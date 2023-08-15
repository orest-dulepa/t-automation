"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const typeorm_1 = require("typeorm");
const boom_1 = require("@hapi/boom");
const db_1 = require("@/utils/db");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const auth_parser_1 = require("@/middlewares/auth-parser");
const ScheduledProcesses_1 = require("@/repositories/ScheduledProcesses");
const scheduled_processes_1 = require("@/@types/scheduled-processes");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const scheduledProcessesRepository = typeorm_1.getCustomRepository(ScheduledProcesses_1.ScheduledProcessesRepository);
    const { id } = event.pathParameters;
    const scheduledProcess = await scheduledProcessesRepository.getById(id);
    if (!scheduledProcess)
        boom_1.notFound(`scheduled process ${id} was not found`);
    await scheduledProcessesRepository.updateStatusById(id, scheduled_processes_1.SCHEDULED_PROCESS_STATUS.CANCELED);
    return {
        statusCode: 201,
        body: {},
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(auth_parser_1.authParser())
    .use(middlewares_1.jsonBodyParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map