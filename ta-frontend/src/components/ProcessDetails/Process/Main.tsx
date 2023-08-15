import React from 'react';
import styled from 'styled-components';

import { IPropertyWithValue } from '@/interfaces/process';
import { ProcessStatus } from '@/interfaces/user-process';

import { formatSeconds } from '@/utils/format-seconds';

import ProcessStatusIcon from '@/components/common/ProcessStatusIcon';
import Time from '@/components/common/Time';
import CurrentDuration from '@/components/common/CurrentDuration';
import Meta from '@/components/common/Meta';

interface IProps {
  status: ProcessStatus;
  name: string;
  createTime: string;
  startTime: string | null;
  endTime: string | null;
  duration: number | null;
  meta: IPropertyWithValue[];
}

const Main: React.FC<IProps> = ({
  status,
  name,
  createTime,
  startTime,
  endTime,
  duration,
  meta,
}) => {
  const renderDuration = () => {
    switch (status) {
      case ProcessStatus.INITIALIZED:
        return '-';
      case ProcessStatus.ACTIVE:
      case ProcessStatus.PROCESSING:
        return <CurrentDuration startTime={startTime} />;
      case ProcessStatus.FAILED:
      case ProcessStatus.WARNING:
      case ProcessStatus.FINISHED:
        return formatSeconds(duration || 0);
      default:
        return '-';
    }
  };

  return (
    <>
      <NameSectionStyled>
        <ProcessStatusIcon status={status} />
        <NameStyled>{name}</NameStyled>
      </NameSectionStyled>

      <InfoSectionStyled>
        <InfoStyled>
          <InfoNameStyled>duration(s)</InfoNameStyled>
          {renderDuration()}
        </InfoStyled>

        <InfoStyled>
          <InfoNameStyled>create time</InfoNameStyled>
          <Time time={createTime} />
        </InfoStyled>

        <InfoStyled>
          <InfoNameStyled>start time</InfoNameStyled>
          <Time time={startTime} />
        </InfoStyled>

        <InfoStyled>
          <InfoNameStyled>end time</InfoNameStyled>
          <Time time={endTime} />
        </InfoStyled>

        <InfoStyled>
          <InfoNameStyled>input</InfoNameStyled>
          <Meta meta={meta} />
        </InfoStyled>
      </InfoSectionStyled>
    </>
  );
};

const NameSectionStyled = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 15px;
`;

const NameStyled = styled.h1`
  margin: 0px 0px 0px 10px;
  font-weight: 500;
`;

const InfoSectionStyled = styled.div`
  display: flex;
  justify-content: space-between;
`;

const InfoStyled = styled.div`
  margin-right: 10px;

  &:last-child {
    margin-right: 0px;
  }
`;

const InfoNameStyled = styled.div`
  text-transform: uppercase;
  padding-bottom: 6px;
  color: #83839c;
  font-size: 12px;
  font-weight: 500;
`;

export default Main;
