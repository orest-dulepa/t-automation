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
const Organization_1 = require("@/repositories/Organization");
const User_2 = require("@/entities/User");
const validator_1 = require("@/middlewares/validator");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const schema_1 = require("./schema");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const userRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
    const organizationRepository = typeorm_1.getCustomRepository(Organization_1.OrganizationRepository);
    let { email, firstName, lastName } = event.body;
    email = email.toLowerCase();
    const domain = email.split('@')[1];
    const subdomain = domain.split('.')[0].toLowerCase();
    const organization = await organizationRepository.getByName(subdomain);
    if (!organization)
        throw boom_1.badRequest('not allowed email');
    const otp = otp_1.generateOTP();
    const user = new User_2.User(email, firstName, lastName, organization);
    user.setOtp(otp);
    await userRepository.insert(user);
    await email_1.sendOtpViaEmail(email, otp, firstName);
    return {
        statusCode: 201,
        body: {},
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(validator_1.validator(schema_1.signUpSchema))
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map