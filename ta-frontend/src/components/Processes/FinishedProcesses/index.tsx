import React from 'react';
import styled from 'styled-components';

import { IUserProcess } from '@/interfaces/user-process';
import { IQueries, SortsFields } from '@/interfaces/filter';

import { formatSeconds } from '@/utils/format-seconds';

import Table from '@/components/common/Table';
import TableHead from '@/components/common/TableHead';
import TableRow from '@/components/common/TableRow';
import TableData from '@/components/common/TableData';
import ProcessStatusIcon from '@/components/common/ProcessStatusIcon';
import Time from '@/components/common/Time';
import Meta from '@/components/common/Meta';

import Sort from './Sort';
import Pagination from './Pagination';

interface IProps {
  handleTryReload: () => void;
  processes: IUserProcess[];
  isLoading: boolean;
  isError: boolean;
  isUserManagerOrAdmin: boolean;
  isUserAdmin: boolean;
  isFinishedProcessesMinorPending: boolean;
  finishedProcessesTotal: number;
  finishedFiltersQueries: IQueries;
  handlePageChange: (page: number) => void;
  handleSortByChange: (sortBy: SortsFields) => void;
  sortByColumn: { column: SortsFields; order: 1 | 0 };
  clearFilters: React.ReactNode;
  filters: React.ReactNode;
}

const FinishedProcesses: React.FC<IProps> = ({
  handleTryReload,
  processes,
  isLoading,
  isError,
  isUserManagerOrAdmin,
  isUserAdmin,
  isFinishedProcessesMinorPending,
  finishedProcessesTotal,
  finishedFiltersQueries,
  handlePageChange,
  handleSortByChange,
  sortByColumn,
  clearFilters,
  filters,
}) => {
  const handleSortableThClick = (sortBy: SortsFields) => () => {
    handleSortByChange(sortBy);
  };

  return (
    <>
      <Table
        name="Finished Processes"
        handleTryReload={handleTryReload}
        isLoading={isLoading}
        isError={isError}
        isMinorLoading={isFinishedProcessesMinorPending}
        isEmpty={!processes.length}
        emptyText="No processes finished"
        isFixedHeight
        nameComponent={clearFilters}
        component={filters}
      >
        <colgroup>
          <col span={1} style={{ maxWidth: '75px', width: '75px' }} />
          <col span={1} style={{ maxWidth: '50%' }} />
          <col span={1} />
          <col span={1} />
          {isUserAdmin && <col span={1} />}
          <col span={1} />
          <col span={1} />
          {isUserManagerOrAdmin && <col span={1} />}
        </colgroup>

        <TableHead>
          <HeaderRow>
            <th>State</th>
            <th>
              <Sort
                onClick={handleSortableThClick(SortsFields.processes)}
                isActive={sortByColumn.column === SortsFields.processes}
                order={sortByColumn.order}
              >
                Process
              </Sort>
            </th>
            <th>Input</th>
            <th>
              <Sort
                onClick={handleSortableThClick(SortsFields.runNumber)}
                isActive={sortByColumn.column === SortsFields.runNumber}
                order={sortByColumn.order}
              >
                Run Number
              </Sort>
            </th>
            {isUserAdmin && <th>Robocloud Run Number</th>}
            <th>
              <Sort
                onClick={handleSortableThClick(SortsFields.duration)}
                isActive={sortByColumn.column === SortsFields.duration}
                order={sortByColumn.order}
              >
                Duration
              </Sort>
            </th>
            <th>
              <Sort
                onClick={handleSortableThClick(SortsFields.endTimes)}
                isActive={sortByColumn.column === SortsFields.endTimes}
                order={sortByColumn.order}
              >
                End Time
              </Sort>
            </th>
            {isUserManagerOrAdmin && (
              <th>
                <Sort
                  onClick={handleSortableThClick(SortsFields.executedBy)}
                  isActive={sortByColumn.column === SortsFields.executedBy}
                  order={sortByColumn.order}
                >
                  Executed by
                </Sort>
              </th>
            )}
          </HeaderRow>
        </TableHead>

        <tbody>
          {processes.map(({
            id,
            status,
            process,
            meta,
            duration,
            endTime,
            user,
            robocorpId,
          }) => (
            <TableRow key={id} id={id}>
              <TableData>
                <ProcessStatusIcon status={status} />
              </TableData>

              <TableData>
                <ProcessRow>{process.name}</ProcessRow>
              </TableData>

              <TableData>
                <Meta meta={meta} />
              </TableData>

              <TableData>{id}</TableData>

              {isUserAdmin && <TableData>{robocorpId}</TableData>}

              <TableData>{formatSeconds(duration!)}</TableData>

              <TableData>
                <Time time={endTime} />
              </TableData>

              {isUserManagerOrAdmin && <TableData>{user.email}</TableData>}
            </TableRow>
          ))}
        </tbody>
      </Table>
      <Pagination
        handlePageChange={handlePageChange}
        finishedFiltersQueries={finishedFiltersQueries}
        finishedProcessesTotal={finishedProcessesTotal}
      />
    </>
  );
};

const ProcessRow = styled.div`
  display: flex;
  align-items: center;
`;

const HeaderRow = styled.tr`
  th {
    position: sticky;
    top: 0;
    z-index: 1;
  }
`;

export default FinishedProcesses;
