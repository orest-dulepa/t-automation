import {APIGatewayProxyWithLambdaAuthorizerHandler} from 'aws-lambda';
import middy from 'middy';
import {cors, doNotWaitForEmptyEventLoop, jsonBodyParser} from 'middy/middlewares';
import {notFound} from '@hapi/boom';
import {getCustomRepository} from 'typeorm';
import {createOrGetDBConnection} from '@/utils/db';
import {errorHandler} from '@/middlewares/error-handler';
import {jsonBodySerializer} from '@/middlewares/json-body-serializer';
import {IProcessChangeStatusRequest, IProcessChangeStatusResponse} from './types';
import {UsersProcessesRepository} from "@/repositories/UsersProcesses";
import {PROCESS_STATUS} from "@/@types/users-processes";

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IProcessChangeStatusRequest,
  IProcessChangeStatusResponse
> = async (event) => {
  console.log('Event: ', event);
  await createOrGetDBConnection();

  const usersProcessesRepository = getCustomRepository(UsersProcessesRepository);

  const { runId, newStatus } = event.body;

  const userProcess = await usersProcessesRepository.getByProcessRunId(runId);

  if (!userProcess) throw notFound('usersProcess was not found');
  if (!Object.values(PROCESS_STATUS).includes(newStatus)) {
    throw notFound('New status is incorrect');
  }

  userProcess.setStatus(newStatus);

  if (newStatus === PROCESS_STATUS.WARNING) {
    userProcess.setEndTime(new Date().toISOString());
    userProcess.setDuration();
  }

  await usersProcessesRepository.update(userProcess);
  console.log(`Set new status ${newStatus} to userProcess ${userProcess.id}`, new Date().toISOString(), new Date().getTime());

  return {
    statusCode: 200,
    body: userProcess
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
