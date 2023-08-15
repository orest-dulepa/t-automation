import {
  APIGatewayTokenAuthorizerEvent,
  Context,
  APIGatewayAuthorizerResult,
  Callback,
} from 'aws-lambda';
import { getCustomRepository } from 'typeorm';

import { UserRepository } from '@/repositories/User';

import { User } from '@/entities/User';

import { ITokenPayload, TOKEN_TYPE } from '@/@types/auth';

import { createOrGetDBConnection } from '@/utils/db';
import { verifyToken } from '@/utils/jwt';

const generatePolicy = (
  principalId: number,
  Effect: string,
  Resource: string,
  { id, email, firstName, lastName, otp, organization, role }: User,
) => ({
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

export const handler = async (
  event: APIGatewayTokenAuthorizerEvent,
  _: Context,
  callback: Callback<APIGatewayAuthorizerResult>,
) => {
  try {
    if (!event.authorizationToken) {
      return callback('Unauthorized');
    }

    const tokenParts = event.authorizationToken.split(' ');
    const tokenValue = tokenParts[1];

    if (!(tokenParts[0].toLowerCase() === 'bearer' && tokenValue)) {
      return callback('Unauthorized');
    }

    const { id, type } = verifyToken(tokenValue) as ITokenPayload;

    if (type !== TOKEN_TYPE.ACCESS_TOKEN) {
      return callback('Unauthorized');
    }

    await createOrGetDBConnection();

    const userRepository = getCustomRepository(UserRepository);

    const user = await userRepository.getByIdWithOrganizationAndRole(id);

    if (!user) {
      return callback('Unauthorized');
    }

    return generatePolicy(id, 'Allow', event.methodArn, user);
  } catch (e) {
    return callback('Unauthorized');
  }
};
