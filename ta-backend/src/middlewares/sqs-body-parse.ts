import { MiddlewareFunction, MiddlewareObject } from 'middy';

export const sqsBodyParse = (): MiddlewareObject<any, any> => {
  const parse: MiddlewareFunction<any, any> = (handler, next) => {
    const { Records } = handler.event;

    Records[0].body = JSON.parse(Records[0].body);

    next();
  };

  return {
    before: parse,
  };
};
