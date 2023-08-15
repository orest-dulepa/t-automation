import moment from 'moment';

/* eslint-disable import/prefer-default-export */
export const getTimelineLabels = (
  desiredStartTime: string, interval: number, period: moment.unitOfTime.Base,
) => {
  const passedTimeToday = moment.duration(desiredStartTime).as(period);

  const leftedPeriodsInADay = moment.duration(1, 'day').as(period) - interval - passedTimeToday;

  const startTimeMoment = moment(desiredStartTime, 'hh:mm');

  const timeLabels = [];

  for (let i = 0; i <= leftedPeriodsInADay; i += interval) {
    startTimeMoment.add(i === 0 ? 0 : interval, period);
    timeLabels.push(startTimeMoment.format('hh:mm A'));
  }

  return timeLabels;
};
