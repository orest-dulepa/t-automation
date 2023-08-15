import React from 'react';
import styled from 'styled-components';

import { IProcess } from '@/interfaces/process';

import Table from '@/components/common/Table';
import TableHead from '@/components/common/TableHead';
import TableData from '@/components/common/TableData';
import Button from '@/components/common/Button';

interface IProps {
  handleTryReload: () => void;
  onStartProcessClick: (id: number) => () => void;
  processes: IProcess[];
  isLoading: boolean;
  isError: boolean;
}

const AvailableProcesses: React.FC<IProps> = ({
  handleTryReload,
  onStartProcessClick,
  processes,
  isLoading,
  isError,
}) => (
  <Table
    name="Processes"
    handleTryReload={handleTryReload}
    isLoading={isLoading}
    isError={isError}
    isEmpty={!processes.length}
    emptyText="No processes"
  >
    <TableHead>
      <tr>
        <th>Process</th>
      </tr>
    </TableHead>

    <tbody>
      {processes.map(({ id, name }) => (
        <tr key={id}>
          <TableData>
            <ProcessRow>
              {name}
              <StartProcessButton onClick={onStartProcessClick(id)}>Run</StartProcessButton>
            </ProcessRow>
          </TableData>
        </tr>
      ))}
    </tbody>
  </Table>
);

const ProcessRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const StartProcessButton = styled(Button)`
  padding: 10px 28px 10px 48px;
  background-image: url('/assets/play.svg');
  border-radius: 30px;
  background-repeat: no-repeat;
  background-position: 12px 50%;
`;

export default AvailableProcesses;
