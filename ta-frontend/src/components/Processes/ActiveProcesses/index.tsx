import React from 'react';
import styled from 'styled-components';

import { IUserProcess } from '@/interfaces/user-process';

import Table from '@/components/common/Table';
import TableHead from '@/components/common/TableHead';
import TableRow from '@/components/common/TableRow';
import TableData from '@/components/common/TableData';
import ProcessStatusIcon from '@/components/common/ProcessStatusIcon';
import Meta from '@/components/common/Meta';
import CurrentDuration from '@/components/common/CurrentDuration';

interface IProps {
  handleTryReload: () => void;
  processes: IUserProcess[];
  isUserManagerOrAdmin: boolean;
  isLoading: boolean;
  isError: boolean;
}

const ActiveProcesses: React.FC<IProps> = ({
  handleTryReload,
  processes,
  isUserManagerOrAdmin,
  isLoading,
  isError,
}) => (
  <Table
    name="Active Processes"
    handleTryReload={handleTryReload}
    isLoading={isLoading}
    isError={isError}
    isEmpty={!processes.length}
    emptyText="No active processes runs"
  >
    <colgroup>
      <col span={1} style={{ maxWidth: '75px', width: '75px' }} />
      <col span={1} style={{ maxWidth: '50%' }} />
      <col span={1} />
      <col span={1} />
      {isUserManagerOrAdmin && <col span={1} />}
    </colgroup>

    <TableHead>
      <tr>
        <th>State</th>
        <th>Process</th>
        <th>Input</th>
        <th>Duration</th>
        {isUserManagerOrAdmin && <th>Executed by</th>}
      </tr>
    </TableHead>

    <tbody>
      {processes.map(({
        id,
        process,
        meta,
        startTime,
        user,
      }) => (
        <TableRow key={id} id={id}>
          <TableData>
            <ProcessStatusIcon />
          </TableData>

          <TableData>
            <ProcessRow>{process.name}</ProcessRow>
          </TableData>

          <TableData>
            <Meta meta={meta} />
          </TableData>

          <TableData>
            <CurrentDuration startTime={startTime} />
          </TableData>

          {isUserManagerOrAdmin && <TableData>{user.email}</TableData>}
        </TableRow>
      ))}
    </tbody>
  </Table>
);

const ProcessRow = styled.div`
  display: flex;
  align-items: center;
`;

export default ActiveProcesses;
