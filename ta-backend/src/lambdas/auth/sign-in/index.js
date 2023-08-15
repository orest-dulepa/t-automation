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
const otp_1 = require("@/utils/otp");
const db_1 = require("@/utils/db");
const email_1 = require("@/utils/email");
const User_1 = require("@/repositories/User");
const validator_1 = require("@/middlewares/validator");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const schema_1 = require("./schema");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const userRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
    const email = event.body.email.toLowerCase();
    const otp = otp_1.generateOTP();
    const { affected } = await userRepository.updateOtpByEmail(email, otp);
    if (!affected)
        throw boom_1.notFound('user was not found');
    let currentUser = await userRepository.getByEmailWithOrganizationAndRole(email);
    await email_1.sendOtpViaEmail(email, otp, currentUser.firstName);
    return {
        statusCode: 200,
        body: {},
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(validator_1.validator(schema_1.signInSchema))
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map