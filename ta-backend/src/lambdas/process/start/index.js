"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const typeorm_1 = require("typeorm");
const process_1 = require("@/@types/process");
const robocorp_1 = require("@/http-clients/robocorp");
const UsersProcesses_1 = require("@/entities/UsersProcesses");
const db_1 = require("@/utils/db");
const User_1 = require("@/repositories/User");
const UsersProcesses_2 = require("@/repositories/UsersProcesses");
const Process_1 = require("@/repositories/Process");
const process_2 = require("@/@types/process");
const aws_1 = require("@/http-clients/aws");
const rawHandler = async (event, context, callback) => {
    console.log('Event: ', event);
    let { processId, userId, meta, dataForBot, changeStatusUrl } = event;
    await db_1.createOrGetDBConnection();
    const processRepository = typeorm_1.getCustomRepository(Process_1.ProcessRepository);
    const usersProcessesRepository = typeorm_1.getCustomRepository(UsersProcesses_2.UsersProcessesRepository);
    const usersRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
    const user = await usersRepository.getByIdWithOrganizationAndRole(Number(userId));
    if (!user)
        return callback(null);
    const process = await processRepository.getById(processId);
    if (!process)
        return callback(null);
    if (process.type === process_1.PROCESS_TYPE.ROBOCORP) {
        if (typeof (dataForBot) == 'undefined') {
            console.log('dataForBot is undefined');
            dataForBot = [];
        }
        dataForBot.push({ name: 'User Email', api_name: 'userEmail', value: String(user.email), type: process_2.PROPERTY_TYPE.text });
        const { id } = await robocorp_1.startRobocorp(process, dataForBot.concat(meta));
        console.log('StartRobocorp id: ', id);
        console.log('Data for bot: ', dataForBot);
        const organization = user.organization;
        const usersProcesses = new UsersProcesses_1.UsersProcesses(id, user, organization, process, meta);
        console.log('usersProcesses', usersProcesses);
        await usersProcessesRepository.insert(usersProcesses);
    }
    if (process.type === process_1.PROCESS_TYPE.AWS) {
        await aws_1.startAWSBot(user, process, meta, changeStatusUrl);
    }
    return callback(null);
};
exports.handler = middy_1.default(rawHandler).use(middlewares_1.doNotWaitForEmptyEventLoop());
//# sourceMappingURL=index.js.map