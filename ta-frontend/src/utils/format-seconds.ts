import moment from 'moment';

/* eslint-disable import/prefer-default-export */
export const formatSeconds = (seconds: number) => {
  const format = seconds >= 3600 ? 'hh:mm:ss' : 'mm:ss';

  return moment.duration(seconds, 'seconds').format(format);
};
