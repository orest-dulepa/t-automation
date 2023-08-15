import { AxiosError } from 'axios';

export const isAxiosError = <T>(e: AxiosError<T> | any): e is AxiosError<T> => {
  if ((e as AxiosError).isAxiosError === undefined) return false;
  return (e as AxiosError).isAxiosError;
};
