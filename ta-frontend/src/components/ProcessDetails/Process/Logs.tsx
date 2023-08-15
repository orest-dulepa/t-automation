import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';

import { IUserProcessDetails } from '@/interfaces/user-process';

interface IProps extends Pick<IUserProcessDetails, 'logs'> {}

const Logs: React.FC<IProps> = ({ logs }) => {
  const logsContainer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logsContainer.current) {
      logsContainer.current!.scrollTop = logsContainer.current.scrollHeight;
    }
  }, [logs, logsContainer]);

  return (
    <>
      <LogsTitleStyled>Log</LogsTitleStyled>
      <LogsContainerStyled ref={logsContainer}>{logs || 'Empty logs'}</LogsContainerStyled>
    </>
  );
};

const LogsTitleStyled = styled.h5`
  color: #83839c;
  text-transform: uppercase;
  font-size: 12px;
  font-weight: 500;
  margin: 0px 0px 12px;
`;

const LogsContainerStyled = styled.div`
  font-size: 16px;
  white-space: pre-line;
  line-height: 1.6;
  color: #192e43;
  max-height: 50vh;
  overflow: auto;
`;

export default Logs;
