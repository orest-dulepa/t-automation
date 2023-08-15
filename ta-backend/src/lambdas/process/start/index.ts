import { Handler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { PROCESS_TYPE } from '@/@types/process';
import { startRobocorp } from '@/http-clients/robocorp';
import { UsersProcesses } from '@/entities/UsersProcesses';
import { createOrGetDBConnection } from '@/utils/db';
import { UserRepository } from '@/repositories/User';
import { UsersProcessesRepository } from '@/repositories/UsersProcesses';
import { ProcessRepository } from '@/repositories/Process';
import { IProcessStartEvent } from './types';
import { PROPERTY_TYPE } from "@/@types/process";
import { startAWSBot } from "@/http-clients/aws";

const rawHandler: Handler<IProcessStartEvent> = async (event, context, callback) => {
  console.log('Event: ', event);
  let { processId, userId, meta, dataForBot, changeStatusUrl } = event;

  await createOrGetDBConnection();
  const processRepository = getCustomRepository(ProcessRepository);
  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);
  const usersRepository = getCustomRepository(UserRepository);

  const user = await usersRepository.getByIdWithOrganizationAndRole(Number(userId));
  if (!user) return callback(null);

  const process = await processRepository.getById(processId);
  if (!process) return callback(null);

  if (process.type === PROCESS_TYPE.ROBOCORP) {
    if (typeof(dataForBot) == 'undefined') {
      console.log('dataForBot is undefined');
      dataForBot = [];
    }
    dataForBot.push(
      { name: 'User Email', api_name: 'userEmail', value: String(user.email), type: PROPERTY_TYPE.text },
    );

    const { id } = await startRobocorp(process, dataForBot.concat(meta));

    console.log('StartRobocorp id: ', id);
    console.log('Data for bot: ', dataForBot);

    const organization = user.organization;
    const usersProcesses = new UsersProcesses(id, user, organization, process, meta);
    console.log('usersProcesses', usersProcesses);

    await usersProcessesRepository.insert(usersProcesses!);
  }

  if (process.type === PROCESS_TYPE.AWS) {
    await startAWSBot(user, process, meta, changeStatusUrl);
  }

  return callback(null);
};

export const handler = middy(rawHandler).use(doNotWaitForEmptyEventLoop());
