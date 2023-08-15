import { MiddlewareFunction, MiddlewareObject } from 'middy';

export const authParser = (): MiddlewareObject<any, any> => {
  const parse: MiddlewareFunction<any, any> = (handler, next) => {
    const { requestContext } = handler.event;

    const { authorizer } = requestContext;

    authorizer.organization = JSON.parse(authorizer.organization);
    authorizer.role = JSON.parse(authorizer.role);

    next();
  };

  return {
    before: parse,
  };
};
