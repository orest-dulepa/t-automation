"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.requestWithRetry = exports.getRobocorpLogs = exports.getRobocorpEvents = exports.downloadArtifact = exports.downloadRobocorpArtifact = exports.getRobocorpArtifacts = exports.monitorRobocorp = exports.startRobocorp = void 0;
const process_1 = require("@/@types/process");
const map_properties_1 = require("@/utils/map-properties");
const create_instance_1 = require("../create-instance");
const axios_1 = __importDefault(require("axios"));
const typeorm_1 = require("typeorm");
const User_1 = require("@/repositories/User");
const jwt_1 = require("@/utils/jwt");
const db_1 = require("@/utils/db");
const boom_1 = require("@hapi/boom");
exports.startRobocorp = async ({ credentials }, body) => {
    const { server, apiProcessId, apiWorkspace, rcWskey } = credentials;
    await db_1.createOrGetDBConnection();
    const headers = {
        Authorization: `RC-WSKEY ${rcWskey}`,
    };
    const userRepository = typeorm_1.getCustomRepository(User_1.UserRepository);
    const robotUser = await userRepository.getByEmailWithOrganizationAndRole('robocloud@ta.com');
    if (!robotUser)
        throw boom_1.forbidden();
    const accessToken = jwt_1.createToken(robotUser.id);
    const refreshToken = jwt_1.createRefreshToken(robotUser.id);
    body.push({ name: 'Access Token', api_name: 'accessToken', value: accessToken, type: process_1.PROPERTY_TYPE.token }, { name: 'Refresh Token', api_name: 'refreshToken', value: refreshToken, type: process_1.PROPERTY_TYPE.token });
    const data = {
        variables: map_properties_1.mapProperties(body),
    };
    const robocorpURL = create_instance_1.createInstance(server + '/workspaces/');
    console.log('robocorpURL', robocorpURL);
    return robocorpURL.post(`/${apiWorkspace}/processes/${apiProcessId}/runs`, data, { headers });
};
exports.monitorRobocorp = ({ server, apiWorkspace, apiProcessId, processRunId, rcWskey, }) => {
    const headers = {
        Authorization: `RC-WSKEY ${rcWskey}`,
    };
    const robocorpURL = create_instance_1.createInstance(server + '/workspaces/');
    console.log('robocorpURL', robocorpURL);
    return robocorpURL.get(`/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}`, {
        headers,
        params: {
            embed: 'robotRuns',
        },
    });
};
exports.getRobocorpArtifacts = ({ server, apiWorkspace, apiProcessId, processRunId, robotRunsId, rcWskey, }) => {
    const headers = {
        Authorization: `RC-WSKEY ${rcWskey}`,
    };
    const robocorpURL = create_instance_1.createInstance(server + '/workspaces/');
    console.log('robocorpURL', robocorpURL);
    return robocorpURL.get(`/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}/robotRuns/${robotRunsId}/artifacts`, {
        headers,
    });
};
exports.downloadRobocorpArtifact = ({ server, apiWorkspace, apiProcessId, processRunId, robotRunsId, artifactId, fileName, rcWskey, }) => {
    const headers = {
        Authorization: `RC-WSKEY ${rcWskey}`,
    };
    const robocorpURL = create_instance_1.createInstance(server + '/workspaces/');
    return robocorpURL.get(`/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}/robotRuns/${robotRunsId}/artifacts/${artifactId}/${fileName}`, {
        headers
    });
};
exports.downloadArtifact = ({ link, }) => {
    return axios_1.default.get(link, { responseType: 'arraybuffer' });
};
exports.getRobocorpEvents = ({ server, apiWorkspace, apiProcessId, processRunId, robotRunsId, rcWskey, }) => {
    const headers = {
        Authorization: `RC-WSKEY ${rcWskey}`,
    };
    const robocorpURL = create_instance_1.createInstance(server + '/workspaces/');
    return robocorpURL.get(`/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}/robotRuns/${robotRunsId}/events`, {
        headers,
    });
};
exports.getRobocorpLogs = ({ server, apiWorkspace, apiProcessId, processRunId, robotRunsId, rcWskey, }) => {
    const headers = {
        Authorization: `RC-WSKEY ${rcWskey}`,
    };
    const robocorpURL = create_instance_1.createInstance(server + '/workspaces/');
    return robocorpURL.get(`/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}/robotRuns/${robotRunsId}/messages`, {
        headers,
    });
};
exports.requestWithRetry = async ({ func, args, }) => {
    try {
        return await func.call(func, args);
    }
    catch (e) {
        console.log(`Error, getting robo logs ${e}`);
    }
    return undefined;
};
//# sourceMappingURL=index.js.map