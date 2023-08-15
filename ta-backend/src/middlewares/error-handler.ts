import { MiddlewareFunction, MiddlewareObject } from 'middy';
import { isBoom } from '@hapi/boom';

export const errorHandler = (): MiddlewareObject<any, any> => {
  const handleError: MiddlewareFunction<any, any> = (handler, next) => {
    const { error } = handler;

    let statusCode: number;
    let msg: string;

    console.log((error as any)?.response?.data?.error);

    if (isBoom(error)) {
      const { output, message } = error;

      statusCode = output.statusCode;
      msg = message;
    } else {
      statusCode = 500;
      msg = error?.message || 'Something went wrong';
    }

    handler.response = {
      statusCode,
      body: JSON.stringify({ msg }),
    };

    next();
  };

  return {
    onError: handleError,
  };
};
