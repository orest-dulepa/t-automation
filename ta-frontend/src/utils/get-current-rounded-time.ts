import moment from 'moment';

const INTERVAL_IN_MINUTES = 30;

/* eslint-disable import/prefer-default-export */
export const getCurrentRoundedTime = (): string => {
  const now = moment();

  if (now.get('m') > INTERVAL_IN_MINUTES) {
    now.set({ minute: 0, hour: now.add(1, 'hours').get('h') });
  } else {
    now.set('minute', INTERVAL_IN_MINUTES);
  }

  return now.format('hh:mm A');
};
