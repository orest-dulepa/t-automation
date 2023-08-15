import React from 'react';
import moment from 'moment';
import styled from 'styled-components';
import { DaysOfWeek } from '@/@types/days-of-week';

interface IProps {
  time: string | null;
  isTimeZoneShown?: boolean;
  daysOfWeek?: DaysOfWeek[];
}

const Time: React.FC<IProps> = ({ time, isTimeZoneShown, daysOfWeek }) => {
  if (!time) return <>-</>;

  return (
    <EndTimeStyled>
      <MainStyled>{ daysOfWeek ? daysOfWeek.join(', ') : moment(time).format('YYYY-MM-DD') }</MainStyled>
      <MinorStyled>
        { moment(time, daysOfWeek ? 'hh:mm' : '').format('HH:mm:ss') }
        { isTimeZoneShown && <span>{moment(time, daysOfWeek ? 'hh:mm' : '').format('Z')}</span> }
      </MinorStyled>
    </EndTimeStyled>
  );
};

const EndTimeStyled = styled.div`
  display: flex;
  align-items: center;
`;

const MainStyled = styled.div`
  white-space: nowrap;
  margin-right: 5px;
`;

const MinorStyled = styled.div`
  white-space: nowrap;
  color: #6c757d;

  span {
    margin-left: 5px;
  }
`;

export default Time;
