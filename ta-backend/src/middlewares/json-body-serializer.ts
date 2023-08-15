import { MiddlewareFunction, MiddlewareObject } from 'middy';

export const jsonBodySerializer = (): MiddlewareObject<any, any> => {
  const serialize: MiddlewareFunction<any, any> = (handler, next) => {
    const { body } = handler.response;

    handler.response.body = typeof body === 'string' ? body : JSON.stringify(body);

    next();
  };

  return {
    after: serialize,
  };
};
