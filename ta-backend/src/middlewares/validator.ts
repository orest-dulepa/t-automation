import { MiddlewareFunction, MiddlewareObject } from 'middy';
import { ObjectSchema } from 'joi';
import { badRequest } from '@hapi/boom';

export const validator = (schema: ObjectSchema): MiddlewareObject<any, any> => {
  const validate: MiddlewareFunction<any, any> = (handler, next) => {
    const { body } = handler.event;

    const { error } = schema.validate(body || {});

    if (error) {
      throw badRequest(error.message);
    }

    next();
  };

  return {
    before: validate,
  };
};
