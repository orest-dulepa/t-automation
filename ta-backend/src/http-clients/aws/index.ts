import { forbidden } from "@hapi/boom";
import { createRefreshToken, createToken } from "@/utils/jwt";
import { uuidv4 } from "@/utils/uuid";
import { UsersProcesses } from "@/entities/UsersProcesses";
import { IAWSBotCredential, IPropertyWithValue } from "@/@types/process";
import { getCustomRepository } from "typeorm";
import { UserRepository } from "@/repositories/User";
import { UsersProcessesRepository } from "@/repositories/UsersProcesses";
import AWS from "aws-sdk";
import { User } from "@/entities/User";
import { Process } from "@/entities/Process";

const stepFunctions = new AWS.StepFunctions();

export const startAWSBot = async (user: User, process: Process, meta: IPropertyWithValue[], changeStatusUrl: string) => {
  const usersRepository = getCustomRepository(UserRepository);
  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);

  const botUser = await usersRepository.getByEmailWithOrganizationAndRole('bot@ta.com');
  if (!botUser) throw forbidden();

  const accessToken = createToken(botUser.id);
  const refreshToken = createRefreshToken(botUser.id);
  const processRunId = uuidv4();
  const organization = user.organization;

  const usersProcesses = new UsersProcesses(processRunId, user, organization, process, meta);
  usersProcesses.setStartTime(new Date().toISOString());
  console.log('usersProcesses', usersProcesses);

  const { ARN } = process.credentials as IAWSBotCredential;
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

  await usersProcessesRepository.insert(usersProcesses!);
}
