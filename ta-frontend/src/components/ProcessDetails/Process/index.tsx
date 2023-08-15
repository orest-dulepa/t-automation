import React from 'react';
import styled from 'styled-components';

import { IUserProcessDetails } from '@/interfaces/user-process';

import Main from './Main';
import Logs from './Logs';
import Events from './Events';
import Artifacts from './Artifacts';

interface IProps {
  downloadArtifact: (key: string) => () => void;
  processDetails: IUserProcessDetails;
  isArtifactDownloading: boolean;
}

const Process: React.FC<IProps> = ({ downloadArtifact, processDetails, isArtifactDownloading }) => (
  <>
    <WrapperStyled>
      <Main
        name={processDetails.process.name}
        status={processDetails.status}
        createTime={processDetails.createTime}
        startTime={processDetails.startTime}
        endTime={processDetails.endTime}
        duration={processDetails.duration}
        meta={processDetails.meta}
      />
    </WrapperStyled>

    <TablesWrapper>
      <Table>
        <Events
          events={processDetails.events.slice().sort((a, b) => Number(a.seqNo) - Number(b.seqNo))}
        />
      </Table>
      <Table>
        <Artifacts
          downloadArtifact={downloadArtifact}
          isArtifactDownloading={isArtifactDownloading}
          artifacts={processDetails.artifacts?.slice().sort(({ key }) => {
            if (key!.endsWith('.log') || key!.endsWith('.error')) return 1;
            return -1;
          })}
        />
      </Table>
    </TablesWrapper>
    <WrapperStyled>
      <Logs logs={processDetails.logs} />
    </WrapperStyled>
  </>
);

const WrapperStyled = styled.div`
  background-color: #fff;
  background: #ffffff;
  border: 1px solid #ebedf2;
  border-radius: 6px;
  padding: 30px;
  margin: 20px 0px 30px;
`;

const TablesWrapper = styled.div`
  display: flex;
`;

const Table = styled.div`
  width: 100%;
  margin-right: 30px;

  &:last-child {
    margin-right: 0px;
  }

  & > div {
    &:first-child {
      margin-bottom: 0px;

      & > div {
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
      }
    }
  }
`;

export default Process;
