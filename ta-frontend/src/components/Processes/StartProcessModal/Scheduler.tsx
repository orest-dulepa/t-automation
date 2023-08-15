import React from 'react';
import moment from 'moment';
import styled from 'styled-components';

import { getCurrentRoundedTime } from '@/utils/get-current-rounded-time';
import { getTimelineLabels } from '@/utils/get-timeline-labels';

import Calendar from '@/components/common/Calendar';
import Select from '@/components/Filters/Select';

interface IProps {
  isSchedulerOpen: boolean;
  selectedTime: string;
  setSelectedTime: React.Dispatch<React.SetStateAction<string>>;
  selectedDate: moment.Moment;
  setSelectedDate: React.Dispatch<React.SetStateAction<moment.Moment>>;
}

const Scheduler: React.FC<IProps> = ({
  isSchedulerOpen, selectedTime, setSelectedTime, selectedDate, setSelectedDate,
}) => {
  const INTERVAL_IN_MINUTES = 30;

  const handleDateChange = (e: Date | Date[]) => {
    setSelectedDate(moment(e as Date));
  };

  const handleScheduledTime = (desiredRunTime: string) => {
    setSelectedTime(desiredRunTime);
  };

  const handleStartTimeForDropdown = () => {
    const isSelectedTodayDate = selectedDate.isSame(moment(), 'day');

    return isSelectedTodayDate
      ? getTimelineLabels(getCurrentRoundedTime().slice(0, -3), INTERVAL_IN_MINUTES, 'm')
      : getTimelineLabels('00:00', INTERVAL_IN_MINUTES, 'm');
  };

  return (
    <>
      {isSchedulerOpen && (
        <SchedulePreferences>
          <Calendar
            handleChange={handleDateChange}
            value={selectedDate.toDate()}
            minDate={new Date()}
          />
          <TimePreferences>
            <p>Schedule run</p>
            <Select
              current={selectedTime}
              list={handleStartTimeForDropdown()
                .map((timelineLabel) => ({ title: timelineLabel, value: timelineLabel }))}
              onChange={handleScheduledTime}
            />
          </TimePreferences>
        </SchedulePreferences>
      )}
    </>
  );
};

const SchedulePreferences = styled.div`
  margin: 20px auto 0;
  width: 350px;
  max-width: 350px;

  .react-calendar,
  .react-calendar__viewContainer {
    border-bottom: none;
    border-bottom-left-radius: unset;
    border-bottom-right-radius: unset;
  }
`;

const TimePreferences = styled.div`
  padding: 12px 16px;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 4px;
  border: 1px solid #f1f2f6;
  background-color: white;
  border-top: 1px solid #f1f2f6;
  border-top-left-radius: unset;
  border-top-right-radius: unset;
  
  >div {
    width: 173px;

    >div:first-child {
      position: relative;
      padding: 12px 10px 12px 49px;
      border-color: #ebedf2;
      border-radius: 11px;

      &.active {
        border-bottom-left-radius: unset;
        border-bottom-right-radius: unset;
        border-bottom: none;
      }

      ::before {
        position: absolute;
        content: '';
        top: 12px;
        left: 10px;
        width: 24px;
        height: 24px;
        mask-image: url('/assets/clock.svg');
        mask-position: center;
        mask-repeat: no-repeat;
        mask-size : contain;
        background-color: #E26F37;
      }

      >div:first-of-type {
        font-weight: 500;
        color: #656565;
      }

      div[class*="ArrowStyled"] {
        width: 24px;
        min-width: 24px;
        height: 24px;
        min-height: 24px;
        mask-image: url('/assets/chevron.svg');
        mask-position: center;
        mask-size: contain;
        mask-repeat: no-repeat;
        background-color: #656565;
      }
    }
  }

  p {
    font-weight: 500;
    line-height: 0;
    color: #656565;
  }
`;

export default Scheduler;
