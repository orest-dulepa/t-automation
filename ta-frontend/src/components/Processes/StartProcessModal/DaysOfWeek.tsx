import React, { useEffect, useState } from 'react';
import { DaysOfWeek as DaysOfWeekEnum } from '@/@types/days-of-week';
import styled from 'styled-components';

interface IDaysOfWeekProps {
  onChange: Function;
}

const DaysOfWeek: React.FC<IDaysOfWeekProps> = ({ onChange }) => {
  const [selectedDays, setSelectedDays] = useState<Array<DaysOfWeekEnum>>([]);

  useEffect(() => {
    onChange(selectedDays);
  }, [selectedDays]);

  const dayClicked = (dayOfWeek: DaysOfWeekEnum) => {
    setSelectedDays((prev) => {
      let selectedValues = prev;

      if (!selectedValues.includes(dayOfWeek)) {
        selectedValues.push(dayOfWeek);
      } else {
        selectedValues = prev.filter((val) => val !== dayOfWeek);
      }

      return [...selectedValues];
    });
  };

  return (
    <DaysOfWeekStyled>
      {
        Object.values(DaysOfWeekEnum).map((dayOfWeek) => (
          <DayStyled
            key={dayOfWeek}
            onClick={() => dayClicked(dayOfWeek)}
            active={selectedDays.includes(dayOfWeek)}
          >
            {dayOfWeek}
          </DayStyled>
        ))
      }

      <RequiredStyled type="text" required value={selectedDays} onChange={() => {}} />
    </DaysOfWeekStyled>
  );
};

const DaysOfWeekStyled = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 25px;
  margin-bottom: 20px;
`;

const DayStyled = styled.div<{ active: boolean }>`
  width: 50px;
  height: 50px;
  text-align: center;
  line-height: 50px;
  background-color: ${({ active }) => (active ? '#f36621' : 'transparent')};
  color: ${({ active }) => (active ? 'white' : '#212529')};
  border: ${({ active }) => (active ? 'none' : '1px solid #E5E5E5')};
  border-radius: 50px;
  cursor: pointer;
  user-select: none;
`;

const RequiredStyled = styled.input`
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 0px;
  height: 0px;
  border: none;
  outline: none;
  user-select: none;
`;

export default DaysOfWeek;
