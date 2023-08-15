import {UsersProcesses} from "@/entities/UsersProcesses";
import {IRobocorpCredential} from "@/@types/process";
import {downloadArtifact, downloadRobocorpArtifact, getRobocorpArtifacts} from "@/http-clients/robocorp";
import AWS from "aws-sdk";

const s3 = new AWS.S3();

export const processArtifacts = async (userProcess: UsersProcesses, robotRunsId: string) => {
  const credentials = userProcess.process.credentials as IRobocorpCredential;
  const processRunId = userProcess.processRunId;

  const artifacts = await getRobocorpArtifacts({processRunId, ...credentials, robotRunsId});
  const downloadPromises = artifacts.map(async ({id: artifactId, fileName}) => {
    const link = await downloadRobocorpArtifact({
      processRunId,
      ...credentials,
      robotRunsId,
      artifactId,
      fileName,
    });

    return (await downloadArtifact({link})).data;
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
}
