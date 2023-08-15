import React, { useEffect, useState } from 'react';
import moment from 'moment';
import styled from 'styled-components';
import { getCurrentRoundedTime } from '@/utils/get-current-rounded-time';
import {
  IProcess, IProperty, IPropertyWithValue, PropertyDataDefaultValues, PropertyType,
} from '@/interfaces/process';
import Error from '@/components/common/Error';
import ToggleSwitch from '@/components/common/ToggleSwitch';
import DaysOfWeek from '@/components/Processes/StartProcessModal/DaysOfWeek';
import RegularTime from '@/components/Processes/StartProcessModal/RegularTime';
import { DaysOfWeek as DaysOfWeekEnum } from '@/@types/days-of-week';
import Property from './Property';
import Scheduler from './Scheduler';
import ButtonsRow from './ButtonsRow';

interface IProps {
  handleCancel: () => void;
  handleSubmit: (
    properties: IPropertyWithValue[], timestamp?: string,
  ) => void;
  handleRegularProcessSubmit: (
    properties: IPropertyWithValue[],
    selectedRegularDaysOfWeek: Array<DaysOfWeekEnum>,
    selectedRegularTime: string,
  ) => void;
  process: IProcess;
  isPending: boolean;
  isRejected: boolean;
}

const StartProcessModal: React.FC<IProps> = ({
  handleCancel,
  handleSubmit,
  handleRegularProcessSubmit,
  process,
  isPending,
  isRejected,
}) => {
  const { properties } = process;

  const mapPropertiesToState = (propertiesToMap: IProperty[]) => (
    propertiesToMap.map((property) => {
      const updatedProperty: IPropertyWithValue = {
        ...property,
        value: '',
      };

      if (property.type === PropertyType.DATE && property.default in PropertyDataDefaultValues) {
        const date = moment();

        if (property.default === PropertyDataDefaultValues.YESTERDAY) {
          date.add(-1, 'days');
        } else if (property.default === PropertyDataDefaultValues.TOMORROW) {
          date.add(1, 'days');
        }

        updatedProperty.value = date.format('MM/DD/YYYY');
      }

      return updatedProperty;
    }));

  const [propertiesWithValue, setPropertiesWithValue] = useState(mapPropertiesToState(properties));

  const [isScheduleToggleOn, setIsScheduleToggleOn] = useState(false);
  const [isRegularToggleOn, setIsRegularToggleOn] = useState(false);

  const [selectedTime, setSelectedTime] = useState(getCurrentRoundedTime());
  const [selectedDate, setSelectedDate] = useState(moment());

  const [
    selectedRegularDaysOfWeek,
    setSelectedRegularDaysOfWeek,
  ] = useState<Array<DaysOfWeekEnum>>([]);
  const [selectedRegularTime, setSelectedRegularTime] = useState('12:00 AM');

  useEffect(() => {
    setSelectedTime(isScheduleToggleOn ? getCurrentRoundedTime() : '');
  }, [isScheduleToggleOn]);

  useEffect(() => {
    const isSelectedTodayDate = selectedDate.isSame(moment(), 'day');

    setSelectedTime(isSelectedTodayDate ? getCurrentRoundedTime() : '12:00 AM');
  }, [selectedDate]);

  useEffect(() => handleCancel, []);

  const getValue = (api_name: string) => {
    const newProperties = propertiesWithValue.find((property) => property.api_name === api_name)!;
    return newProperties.value;
  };

  const setValue = (api_name: string) => (value: string) => {
    const newProperties = propertiesWithValue.map((property) => {
      const updatedProperty = property;

      if (property.api_name === api_name) {
        updatedProperty.value = value;
      }

      return updatedProperty;
    });

    setPropertiesWithValue(newProperties);
  };

  const handleToggleState = () => {
    setIsRegularToggleOn(false);
    setIsScheduleToggleOn((prev) => !prev);
  };

  const handleRegularToggleState = () => {
    setIsScheduleToggleOn(false);
    setIsRegularToggleOn((prev) => !prev);
  };

  const getFullScheduledDate = () => {
    const scheduleTime = moment(selectedTime, 'LT');
    const scheduleDate = moment(selectedDate)
      .set({
        hour: scheduleTime.get('hour'),
        minute: scheduleTime.get('minute'),
        second: 0,
        millisecond: 0,
      });

    return scheduleDate.format();
  };

  const getSubmitContent = (): string => {
    if (isScheduleToggleOn) return 'Schedule';
    if (isRegularToggleOn) return 'Regular';

    return 'Run';
  };

  const internalHandleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (isScheduleToggleOn) {
      handleSubmit(propertiesWithValue, getFullScheduledDate());
    } else if (isRegularToggleOn) {
      handleRegularProcessSubmit(
        propertiesWithValue, selectedRegularDaysOfWeek, selectedRegularTime,
      );
    } else {
      handleSubmit(propertiesWithValue);
    }
  };

  return (
    <StyledForm
      onSubmit={internalHandleSubmit}
    >
      {
        properties.map((property) => (
          <Property
            key={property.api_name}
            value={getValue(property.api_name)}
            defaultVal={property.default}
            onChange={setValue(property.api_name)}
            {...property}
          />
        ))
      }

      <Wrapper>
        <Controllers>
          <SchedulerAndRegularController>
            <p>One-time Schedule</p>
            <ToggleSwitch isToggleOn={isScheduleToggleOn} handleToggleState={handleToggleState} />
          </SchedulerAndRegularController>

          <SchedulerAndRegularController>
            <p>Reoccurring Schedule</p>
            <ToggleSwitch
              isToggleOn={isRegularToggleOn}
              handleToggleState={handleRegularToggleState}
            />
          </SchedulerAndRegularController>
        </Controllers>

        <Scheduler
          isSchedulerOpen={isScheduleToggleOn}
          selectedTime={selectedTime}
          setSelectedTime={setSelectedTime}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
        />

        { isRegularToggleOn && <DaysOfWeek onChange={setSelectedRegularDaysOfWeek} /> }
        { isRegularToggleOn && <RegularTime onChange={setSelectedRegularTime} /> }

        <ButtonsRow
          handleCancel={handleCancel}
          isPending={isPending}
          submitContent={getSubmitContent()}
        />
      </Wrapper>

      {isRejected && <Error>Something went wrong :(</Error>}
    </StyledForm>
  );
};

const StyledForm = styled.form`
  padding: 20px 20px 25px 20px;
  max-width: 500px;
  width: 500px;
`;

const Wrapper = styled.div`
  position: relative;
`;

const Controllers = styled.div`
  display: flex;
  width: 100%;
  align-items: center;

  p {
    margin-right: 15px;
    font-weight: 500;
    font-size: 14px;
    line-height: 16px;
    color: #656565;
  }
`;

const SchedulerAndRegularController = styled.div`
  display: flex;
  align-items: center;
  margin-right: 40px;
`;

export default StartProcessModal;
