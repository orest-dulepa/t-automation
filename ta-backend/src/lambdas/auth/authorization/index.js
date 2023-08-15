"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const typeorm_1 = require("typeorm");
const User_1 = require("@/repositories/User");
const auth_1 = require("@/@types/auth");
const db_1 = require("@/utils/db");
const jwt_1 = require("@/utils/jwt");
const generatePolicy = (principalId, Effect, Resource, { id, email, firstName, lastName, otp, organization, role }) => ({
    principalId: String(principalId),
    policyDocument: {
        Version: '2012-10-17',
        Statement: [
            {
                Action: 'execute-api:Invoke',
                Effect,
                Resource: '*',
            },
        ],
    },
    context: {
        id,
        email,
        firstName,
        lastName,
        otp,
        organization: JSON.stringify(organization),
        role: JSON.stringify(role),
    },
});
exports.handler = async (event, _, callback) => {
    try {
        if (!event.authorizationToken) {
            return callback('Unauthorized');
        }
        const tokenParts = event.authorizationToken.split(' ');
        const tokenValue = tokenParts[1];
        if (!(tokenParts[0].toLowerCase() === 'bearer' && tokenValue)) {
            return callback('Unauthorized');
        }
        const { id, type } = jwt_1.verifyToken(tokenValue);
        if (type !== auth_1.TOKEN_TYPE.ACCESS_TOKEN) {
            return callback('Unauthorized');
        }
        await db_1.createOrGetDBConnection();
        const userRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
        const user = await userRepository.getByIdWithOrganizationAndRole(id);
        if (!user) {
            return callback('Unauthorized');
        }
        return generatePolicy(id, 'Allow', event.methodArn, user);
    }
    catch (e) {
        return callback('Unauthorized');
    }
};
//# sourceMappingURL=index.js.map