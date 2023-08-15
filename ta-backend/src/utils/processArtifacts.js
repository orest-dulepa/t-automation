"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.processArtifacts = void 0;
const robocorp_1 = require("@/http-clients/robocorp");
const aws_sdk_1 = __importDefault(require("aws-sdk"));
const s3 = new aws_sdk_1.default.S3();
exports.processArtifacts = async (userProcess, robotRunsId) => {
    const credentials = userProcess.process.credentials;
    const processRunId = userProcess.processRunId;
    const artifacts = await robocorp_1.getRobocorpArtifacts({ processRunId, ...credentials, robotRunsId });
    const downloadPromises = artifacts.map(async ({ id: artifactId, fileName }) => {
        const link = await robocorp_1.downloadRobocorpArtifact({
            processRunId,
            ...credentials,
            robotRunsId,
            artifactId,
            fileName,
        });
        return (await robocorp_1.downloadArtifact({ link })).data;
    });
    const artifactsBody = await Promise.all(downloadPromises);
    const savePromises = artifactsBody.map((body, i) => {
        return s3
            .upload({
            Bucket: process.env.BUCKET_NAME,
            Key: `${processRunId}/${artifacts[i].fileName}`,
            Body: Buffer.from(body),
        })
            .promise();
    });
    await Promise.all(savePromises);
};
//# sourceMappingURL=processArtifacts.js.map