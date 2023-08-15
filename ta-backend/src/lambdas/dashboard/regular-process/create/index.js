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
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const auth_parser_1 = require("@/middlewares/auth-parser");
const RegularProcess_1 = require("@/entities/RegularProcess");
const User_1 = require("@/repositories/User");
const boom_1 = require("@hapi/boom");
const Process_1 = require("@/repositories/Process");
const RegularProcess_2 = require("@/repositories/RegularProcess");
const rawHandler = async (event) => {
    console.log('Event: ', event);
    const { body, requestContext } = event;
    const { processId, meta, daysOfWeek, startTime } = body;
    if (daysOfWeek.length === 0)
        throw boom_1.badRequest('Time was not set');
    await db_1.createOrGetDBConnection();
    const usersRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
    const processRepository = typeorm_1.getCustomRepository(Process_1.ProcessRepository);
    const regularProcessRepository = typeorm_1.getCustomRepository(RegularProcess_2.RegularProcessRepository);
    const user = await usersRepository.getByIdWithOrganizationAndRole(requestContext.authorizer.id);
    if (!user)
        throw boom_1.notFound('User was not found');
    const process = await processRepository.getById(processId);
    if (!process)
        throw boom_1.notFound('Process was not found');
    const organization = user.organization;
    const regularProcess = new RegularProcess_1.RegularProcess(daysOfWeek, startTime, meta, user, process, organization);
    await regularProcessRepository.insert(regularProcess);
    // for (const dayOfWeek of daysOfWeek) {
    //   await regularProcessTimeRepository.insert(
    //     new RegularProcessTime(dayOfWeek, startTime, regularProcess)
    //   );
    // }
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