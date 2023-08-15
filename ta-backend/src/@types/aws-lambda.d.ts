import {
  Handler,
  APIGatewayProxyEvent,
  APIGatewayProxyResult,
  APIGatewayProxyEventBase,
  SQSRecord,
} from 'aws-lambda';

import { User } from '@/entities/User';

declare module 'aws-lambda' {
  interface CustomAPIGatewayProxyEvent<T> extends APIGatewayProxyEvent {
    body: T;
  }

  interface CustomAPIGatewayProxyResult<T> extends APIGatewayProxyResult {
    body: T;
  }

  type APIGatewayProxyHandler<T = {}, R = {}> = Handler<
    CustomAPIGatewayProxyEvent<T>,
    CustomAPIGatewayProxyResult<R>
  >;

  type APIGatewayEventLambdaAuthorizerContext<TAuthorizerContext> = {
    [P in keyof TAuthorizerContext]: TAuthorizerContext[P] extends null
      ? null
      : TAuthorizerContext[P];
  } & {
    principalId: string;
    integrationLatency: number;
  };

  interface CustomAPIGatewayProxyEventBase<T, P, Q>
    extends APIGatewayProxyEventBase<APIGatewayEventLambdaAuthorizerContext<User>> {
    body: T;
    pathParameters: P;
    queryStringParameters: Q;
  }

  type APIGatewayProxyWithLambdaAuthorizerHandler<T = {}, R = {}, P = {}, Q = {}> = Handler<
    CustomAPIGatewayProxyEventBase<T, P, Q>,
    CustomAPIGatewayProxyResult<R>
  >;

  interface CustomSQSRecord<T> extends SQSRecord {
    body: T;
  }

  interface CustomSQSEvent<T> extends SQSEvent {
    Records: CustomSQSRecord<T>[];
  }

  type SQSHandler<T> = Handler<CustomSQSEvent<T>, void>;
}
