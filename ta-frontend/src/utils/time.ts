import moment from 'moment';

export const localToUTC = (time12: string): string => {
  const time24 = moment(time12, 'hh:mm A').format('HH:mm');
  const h24 = time24.split(':')[0];
  const m24 = time24.split(':')[1];

  const now = new Date();
  now.setHours(Number(h24));
  now.setMinutes(Number(m24));

  return `${now.getUTCHours()}:${now.getUTCMinutes()}`;
};

export const UTCToLocal = (time24: string): string => {
  const h24 = time24.split(':')[0];
  const m24 = time24.split(':')[1];

  const now = new Date();
  now.setUTCHours(Number(h24));
  now.setUTCMinutes(Number(m24));

  return `${now.getHours()}:${now.getMinutes()}`;
};
