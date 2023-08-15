import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import middy from 'middy';
import { doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { getCustomRepository } from 'typeorm';
import { createOrGetDBConnection } from '@/utils/db';
import { ROLE } from '@/@types/role';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';
import { authParser } from '@/middlewares/auth-parser';
import { RegularProcessRepository } from '@/repositories/RegularProcess';
import { IGetRegularProcessesResponse } from './types';


const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<{}, IGetRegularProcessesResponse> = async (
  event,
) => {
  await createOrGetDBConnection();

  const regularProcessesRepository = getCustomRepository(RegularProcessRepository);

  const { authorizer: user } = event.requestContext;
  const { id: userId, organization, role } = user;
  const { id: organizationId, name: organizationName } = organization;
  const { id: roleId } = role;

  const isManager = roleId === ROLE.MANAGER;
  const isAdmin = (roleId === ROLE.ADMIN && organizationName === 'ta');

  let organizationIdToSearch: number | undefined;
  let userIdToSearch: number | undefined;

  if (isManager) {
    organizationIdToSearch = organizationId;
  }

  if (!isAdmin && !isManager) {
    userIdToSearch = userId;
  }

  const scheduledProcesses = await regularProcessesRepository.getAllRegular(organizationIdToSearch, userIdToSearch);

  return {
    statusCode: 200,
    body: scheduledProcesses,
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(authParser())
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
