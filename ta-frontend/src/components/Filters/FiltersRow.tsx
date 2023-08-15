import React, { useState } from 'react';
import styled from 'styled-components';
import moment from 'moment';

import { IProcess } from '@/interfaces/process';
import { FiltersFields } from '@/interfaces/filter';
import { IUser } from '@/interfaces/user';

import Calendar from '@/components/common/Calendar';
import ClickOutsideWrapper from '@/components/common/ClickOutsideWrapper';

import Select from './Select';
import Input from './Input';
import Arrow from './Arrow';

interface IProps {
  finishedFiltersProcesses: IProcess[];
  addFilter: (query: FiltersFields) => (value: string) => void;
  finishedFiltersUsers: IUser[];
  isUserManagerOrAdmin: boolean;
}

const FiltersRow: React.FC<IProps> = ({
  finishedFiltersProcesses,
  addFilter,
  finishedFiltersUsers,
  isUserManagerOrAdmin,
}) => {
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  const handleDateChange = (e: Date | Date[]) => {
    if ((e as Date[]).length === 2) {
      const [from, to] = e as Date[];

      from.setHours(0, 0, 0, 0);
      to.setHours(0, 0, 0, 0);

      const fromInUtc = from.getTime() - from.getTimezoneOffset() * 60000;
      const toInUtc = to.getTime() - to.getTimezoneOffset() * 60000;

      const value = moment(from).isSame(to) ? String(fromInUtc) : `${fromInUtc}-${toInUtc}`;

      addFilter(FiltersFields.endTimes)(value);
      setIsCalendarOpen(false);
    }
  };

  const handleDateLabelClick = (duration: number, format: 'day' | 'days' | 'month' | 'months') => (
    e: React.MouseEvent,
  ) => {
    e.stopPropagation();

    if (format === 'day') {
      const day = moment().subtract(duration, format).toDate();

      handleDateChange([day, day]);
      return;
    }

    const from = moment().subtract(duration, format).toDate();
    const to = moment().toDate();

    handleDateChange([from, to]);
  };

  const openCalendar = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();

    setIsCalendarOpen(true);
  };

  const closeCalendar = (e: Event) => {
    e.stopPropagation();
    e.preventDefault();

    setIsCalendarOpen(false);
  };

  return (
    <FiltersRowStyled>
      <FilterWrapperStyled>
        <Select
          current="Process name"
          list={finishedFiltersProcesses.map(({ name, id }) => ({ title: name, value: id }))}
          onChange={addFilter(FiltersFields.processes)}
        />
      </FilterWrapperStyled>
      <FilterWrapperStyled>
        <Select
          current="State"
          list={[
            { title: 'Success', value: 'finished' },
            { title: 'Failed', value: 'failed' },
            { title: 'Warning', value: 'warning' },
          ]}
          onChange={addFilter(FiltersFields.statuses)}
        />
      </FilterWrapperStyled>
      <FilterWrapperStyled>
        <Input onChange={addFilter(FiltersFields.inputs)} />
      </FilterWrapperStyled>
      <FilterWrapperStyled>
        <CalendarDateStyled onClick={openCalendar} isOpen={isCalendarOpen}>
          End time
          <Arrow isOpen={isCalendarOpen} />
          {isCalendarOpen && (
            <CalendarForFilters handleClose={closeCalendar}>
              <Calendar
                handleChange={handleDateChange}
                allowPartialRange
                selectRange
                returnValue="range"
              />
              <CalendarIntervals>
                <div>
                  <div onClick={handleDateLabelClick(1, 'day')}>1 Day Ago</div>
                  <div onClick={handleDateLabelClick(7, 'days')}>1 Week Ago</div>
                </div>
                <div>
                  <div onClick={handleDateLabelClick(1, 'month')}>1 Month Ago</div>
                  <div onClick={handleDateLabelClick(3, 'months')}>3 Months Ago</div>
                </div>
              </CalendarIntervals>
            </CalendarForFilters>
          )}
        </CalendarDateStyled>
      </FilterWrapperStyled>
      {isUserManagerOrAdmin && (
        <FilterWrapperStyled>
          <Select
            current="Executed by"
            list={finishedFiltersUsers.map(({ email, id }) => ({ title: email, value: id }))}
            onChange={addFilter(FiltersFields.executedBy)}
          />
        </FilterWrapperStyled>
      )}
    </FiltersRowStyled>
  );
};

const CalendarForFilters = styled(ClickOutsideWrapper)`
  position: absolute;
  top: calc(100% + 2px);
  left: 0px;
  z-index: 10;

  .react-calendar,
  .react-calendar__viewContainer {
    border-bottom: none;
    border-bottom-left-radius: unset;
    border-bottom-right-radius: unset;
  }
`;

const CalendarIntervals = styled.div`
  padding: 10px 0;
  display: flex;
  justify-content: space-between;
  border-radius: 4px;
  border: 1px solid #f1f2f6;
  background-color: white;
  border-top: 1px solid #f1f2f6;
  border-top-left-radius: unset;
  border-top-right-radius: unset;

  div {
    width: auto;

    div {
      padding: 6px 16px;
      line-height: 18.4px;
    }

    div:hover {
      background-color: #e6e6e6;
    }
  }

  div:last-child() {
    text-align: right;
  }
`;

const FiltersRowStyled = styled.div`
  display: flex;
  align-items: center;
`;

const FilterWrapperStyled = styled.div`
  margin-right: 15px;

  &:last-child {
    margin-right: 0px;
  }
`;

const CalendarDateStyled = styled.div<{ isOpen: boolean }>`
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 16px;
  min-height: 46px;
  font-size: 1rem;
  line-height: 1.5;
  color: #8b88a2;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid #ebedf2;
  border-radius: 4px;
  position: relative;
  white-space: nowrap;
  cursor: pointer;

  border-color: ${({ isOpen }) => (isOpen ? '#ff5000' : '#ebedf2')};
`;

export default FiltersRow;
