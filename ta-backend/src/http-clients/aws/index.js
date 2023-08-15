"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.startAWSBot = void 0;
const boom_1 = require("@hapi/boom");
const jwt_1 = require("@/utils/jwt");
const uuid_1 = require("@/utils/uuid");
const UsersProcesses_1 = require("@/entities/UsersProcesses");
const typeorm_1 = require("typeorm");
const User_1 = require("@/repositories/User");
const UsersProcesses_2 = require("@/repositories/UsersProcesses");
const aws_sdk_1 = __importDefault(require("aws-sdk"));
const stepFunctions = new aws_sdk_1.default.StepFunctions();
exports.startAWSBot = async (user, process, meta, changeStatusUrl) => {
    const usersRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_2.UsersProcessesRepository);
    const botUser = await usersRepository.getByEmailWithOrganizationAndRole('bot@ta.com');
    if (!botUser)
        throw boom_1.forbidden();
    const accessToken = jwt_1.createToken(botUser.id);
    const refreshToken = jwt_1.createRefreshToken(botUser.id);
    const processRunId = uuid_1.uuidv4();
    const organization = user.organization;
    const usersProcesses = new UsersProcesses_1.UsersProcesses(processRunId, user, organization, process, meta);
    usersProcesses.setStartTime(new Date().toISOString());
    console.log('usersProcesses', usersProcesses);
    const { ARN } = process.credentials;
    const payload = {
        stateMachineArn: ARN,
        input: JSON.stringify({
            processRunId,
            userEmail: user.email,
            accessToken,
            refreshToken,
            changeStatusUrl,
            meta,
        }),
    };
    console.log('Payload: ', payload);
    stepFunctions
        .startExecution(payload)
        .promise()
        .catch((e) => console.log(e));
    console.log('ProcessRunId: ', processRunId);
    await usersProcessesRepository.insert(usersProcesses);
};
//# sourceMappingURL=index.js.map