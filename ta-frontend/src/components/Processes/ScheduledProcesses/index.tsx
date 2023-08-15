import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import moment from 'moment';
import styled from 'styled-components';

import {
  cancelScheduledProcessActions,
  cancelScheduledProcessAsync,
  setScheduledProcessIdAsync,
} from '@/store/actions/cancel-scheduled-process';
import {
  removeRegularProcessActions,
  removeRegularProcessAsync,
  setRegularProcessIdAsync,
} from '@/store/actions/remove-regular-process';

import {
  selectCancelScheduledProcessId,
  selectIsCancelScheduledProcessesPending,
  selectIsCancelScheduledProcessesRejected,
} from '@/store/selectors/cancel-scheduled-process';
import {
  selectIsRemoveRegularProcessesPending, selectIsRemoveRegularProcessesRejected,
  selectRemoveRegularProcessId,
} from '@/store/selectors/remove-regular-process';

import Table from '@/components/common/Table';
import TableHead from '@/components/common/TableHead';
import TableData from '@/components/common/TableData';
import ProcessStatusIcon from '@/components/common/ProcessStatusIcon';
import Time from '@/components/common/Time';
import Button from '@/components/common/Button';
import Meta from '@/components/common/Meta';
import Modal from '@/components/common/Modal';

import { IScheduledProcess } from '@/interfaces/scheduled-process';
import { IRegularProcess } from '@/interfaces/regular-process';
import { ProcessStatus } from '@/interfaces/user-process';
import { UTCToLocal } from '@/utils/time';
import CancelScheduledOrRegularProcessModal from './CancelScheduledOrRegularProcessModal';

interface IProps {
  handleTryReload: () => void;
  processes: IScheduledProcess[];
  regularProcesses: IRegularProcess[];
  isLoading: boolean;
  isError: boolean;
  isUserManagerOrAdmin: boolean;
}

const ScheduledProcesses: React.FC<IProps> = ({
  handleTryReload,
  processes,
  regularProcesses,
  isLoading,
  isError,
  isUserManagerOrAdmin,
}) => {
  const dispatch = useDispatch();

  const isCancelScheduledProcessesPending = useSelector(selectIsCancelScheduledProcessesPending);
  const isCancelScheduledProcessesRejected = useSelector(selectIsCancelScheduledProcessesRejected);
  const cancelScheduledProcessId = useSelector(selectCancelScheduledProcessId);

  const isRemoveRegularProcessesPending = useSelector(selectIsRemoveRegularProcessesPending);
  const isRemoveRegularProcessesRejected = useSelector(selectIsRemoveRegularProcessesRejected);
  const removeRegularProcessId = useSelector(selectRemoveRegularProcessId);

  const handleCancelScheduledProcess = (id: number) => () => {
    dispatch(setScheduledProcessIdAsync(id));
  };
  const handleScheduledModalClose = () => {
    dispatch(cancelScheduledProcessActions.reset());
  };
  const handleScheduledProcessDelete = () => {
    dispatch(cancelScheduledProcessAsync());
  };

  const handleRemoveRegularProcess = (id: number) => () => {
    dispatch(setRegularProcessIdAsync(id));
  };
  const handleRegularModalClose = () => {
    dispatch(removeRegularProcessActions.reset());
  };
  const handleRegularProcessDelete = () => {
    dispatch(removeRegularProcessAsync());
  };

  return (
    <>
      <Table
        name="Scheduled Processes"
        handleTryReload={handleTryReload}
        isLoading={isLoading}
        isError={isError}
        isEmpty={!processes.length && !regularProcesses.length}
        emptyText="No processes scheduled"
        isFixedHeight
      >
        <colgroup>
          <col span={1} style={{ maxWidth: '75px', width: '75px' }} />
          <col span={1} style={{ maxWidth: '50%' }} />
          <col span={1} />
          {isUserManagerOrAdmin && <col span={1} />}
          <col span={1} />
        </colgroup>

        <TableHead>
          <HeaderRow>
            <th>State</th>
            <th>Process</th>
            <th>Input</th>
            {isUserManagerOrAdmin && <th>Executed by</th>}
            <th>Scheduled for</th>
          </HeaderRow>
        </TableHead>

        <tbody>
          {
            processes.map(({
              id,
              status,
              process,
              meta,
              startTime,
              user,
            }) => (
              <tr key={id}>
                <TableData>
                  <ProcessStatusIcon status={status} />
                </TableData>

                <TableData>
                  <ProcessRow>{process.name}</ProcessRow>
                </TableData>

                <TableData>
                  <Meta meta={meta} />
                </TableData>

                {isUserManagerOrAdmin && <TableData>{user.email}</TableData>}

                <TableData>
                  <TableDataWrapper>
                    <Time time={moment(Number(startTime)).format()} isTimeZoneShown />
                    <CancelScheduledOrRegularProcessButton
                      onClick={handleCancelScheduledProcess(id)}
                    >
                      Cancel
                    </CancelScheduledOrRegularProcessButton>
                  </TableDataWrapper>
                </TableData>
              </tr>
            ))
          }

          {
            regularProcesses.map(({
              id,
              daysOfWeek,
              startTime,
              process,
              meta,
              user,
            }) => (
              <tr key={id}>
                <TableData>
                  <ProcessStatusIcon status={ProcessStatus.REGULAR} />
                </TableData>

                <TableData>
                  <ProcessRow>{process.name}</ProcessRow>
                </TableData>

                <TableData>
                  <Meta meta={meta} />
                </TableData>

                { isUserManagerOrAdmin && <TableData>{user.email}</TableData> }

                <TableData>
                  <TableDataWrapper>
                    <Time time={UTCToLocal(startTime)} isTimeZoneShown daysOfWeek={daysOfWeek} />
                    <CancelScheduledOrRegularProcessButton onClick={handleRemoveRegularProcess(id)}>
                      Remove
                    </CancelScheduledOrRegularProcessButton>
                  </TableDataWrapper>
                </TableData>
              </tr>
            ))
          }
        </tbody>
      </Table>

      {
        cancelScheduledProcessId && (
        <Modal onBackdropClick={handleScheduledModalClose} verticallyCentered>
          <CancelScheduledOrRegularProcessModal
            isScheduled
            onClose={handleScheduledModalClose}
            onDelete={handleScheduledProcessDelete}
            isPending={isCancelScheduledProcessesPending}
            isRejected={isCancelScheduledProcessesRejected}
          />
        </Modal>
        )
      }

      {
        removeRegularProcessId && (
        <Modal onBackdropClick={handleRegularModalClose} verticallyCentered>
          <CancelScheduledOrRegularProcessModal
            onClose={handleRegularModalClose}
            onDelete={handleRegularProcessDelete}
            isPending={isRemoveRegularProcessesPending}
            isRejected={isRemoveRegularProcessesRejected}
          />
        </Modal>
        )
      }
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

const TableDataWrapper = styled.div`
  display: flex;
  justify-content: space-between;
`;

const CancelScheduledOrRegularProcessButton = styled(Button)`
  padding: 10px 28px 10px 48px;
  background-image: url('/assets/cancel-in-circle.svg');
  border-radius: 30px;
  background-repeat: no-repeat;
  background-position: 14px 50%;
`;

export default ScheduledProcesses;
