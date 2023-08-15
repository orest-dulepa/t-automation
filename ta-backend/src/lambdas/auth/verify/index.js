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
const jwt_1 = require("@/utils/jwt");
const User_1 = require("@/repositories/User");
const validator_1 = require("@/middlewares/validator");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const schema_1 = require("./schema");
const rawHandler = async (event) => {
    await db_1.createOrGetDBConnection();
    const userRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
    let { email, otp } = event.body;
    email = email.toLowerCase();
    const user = await userRepository.getByEmailWithOrganizationAndRole(email);
    if (!user || (user === null || user === void 0 ? void 0 : user.otp) !== otp)
        throw boom_1.forbidden();
    await userRepository.updateOtpByEmail(email, null);
    const accessToken = jwt_1.createToken(user.id);
    const refreshToken = jwt_1.createRefreshToken(user.id);
    return {
        statusCode: 200,
        body: {
            user: {
                id: user.id,
                firstName: user.firstName,
                lastName: user.lastName,
                email: user.email,
                role: user.role,
                organization: user.organization
            },
            accessToken,
            refreshToken,
        },
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(validator_1.validator(schema_1.verifySchema))
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map