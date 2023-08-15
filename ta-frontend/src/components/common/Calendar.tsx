import React from 'react';
import ReactCalendar from 'react-calendar';
import styled from 'styled-components';

import 'react-calendar/dist/Calendar.css';

interface IProps {
  handleChange: (e: Date | Date[]) => void;
  value?: Date;
  allowPartialRange?: boolean;
  selectRange?: boolean;
  returnValue?: 'start' | 'range';
  minDate?: Date;
}

const Calendar: React.FC<IProps> = ({
  handleChange,
  value,
  allowPartialRange,
  selectRange,
  returnValue = 'start',
  minDate,
}) => (
  <CssFixes>
    <ReactCalendar
      onChange={handleChange}
      value={value}
      allowPartialRange={allowPartialRange}
      selectRange={selectRange}
      returnValue={returnValue}
      minDate={minDate}
    />
  </CssFixes>
);

const CssFixes = styled.div`
  .react-calendar {
    border-color: #f1f2f6;
    border-radius: 4px;
    color: #8b88a2;
    overflow: hidden;
  }

  .react-calendar__navigation button {
    color: #8b88a2;
  }

  .react-calendar__navigation__label {
    color: #8b88a2;
  }

  .react-calendar__month-view__weekdays__weekday {
    color: #c4c4c4;

    abbr {
      text-decoration: none;
    }
  }

  .react-calendar__month-view__weekdays {
    border-bottom: 1px solid #f1f2f6;
  }

  .react-calendar__month-view__days__day {
    color: #8b88a2;
  }

  .react-calendar__month-view__days__day--neighboringMonth {
    color: #c4c4c4;
  }

  .react-calendar__tile {
    &:enabled:hover {
      background-color: #e6e6e6 !important;
    }

    &:focus {
      background-color: initial;
    }
  }

  .react-calendar__tile--now {
    position: relative;
    background: transparent;

    &:after {
      content: '';
      border: 1px solid #ff5000;
      z-index: 0;
      position: absolute;
      top: 50%;
      left: 50%;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      transform: translate(-50%, -50%);
    }
  }

  .react-calendar__tile--active {
    background: white;
    color: white;
    position: relative;
    z-index: 1;

    abbr {
      text-decoration: none;
      position: relative;
      z-index: 1;
    }

    &:after {
      content: '';
      background: #ff5000;
      z-index: 0;
      position: absolute;
      top: 50%;
      left: 50%;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      transform: translate(-50%, -50%);
    }
  }
`;

export default Calendar;
