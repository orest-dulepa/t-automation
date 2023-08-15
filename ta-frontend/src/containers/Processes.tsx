import React, { useEffect } from 'react';
import { Helmet } from 'react-helmet';
import { useDispatch, useSelector } from 'react-redux';
import styled from 'styled-components';
import { IPropertyWithValue } from '@/interfaces/process';
import { SortsFields } from '@/interfaces/filter';
import { loadAvailableProcesses } from '@/store/actions/available-processes';

import {
  startProcessActions,
  setProcessAsync,
  startProcessAsync,
  scheduleProcessAsync, createRegularProcessAsync,
} from '@/store/actions/start-process';

import { loadRegularProcesses, loadScheduledProcesses } from '@/store/actions/scheduled-processes';
import { loadActiveProcesses } from '@/store/actions/active-processes';
import { loadFinishedProcesses } from '@/store/actions/finished-processes';

import {
  loadFilters,
  changePageAsync,
  changeSortByAsync,
  clearFiltersAsync,
} from '@/store/actions/filters';

import {
  selectAvailableProcesses,
  selectIsAvailableProcessesPending,
  selectIsAvailableProcessesRejected,
} from '@/store/selectors/available-processes';
import {
  selectScheduledProcesses,
  selectIsScheduledProcessesPending,
  selectIsScheduledProcessesRejected,
} from '@/store/selectors/scheduled-processes';
import {
  // selectIsRegularProcessesPending,
  // selectIsRegularProcessesRejected,
  selectRegularProcesses,
} from '@/store/selectors/regular-processes';
import {
  selectIsStartProcess,
  selectIsStartProcessPending,
  selectIsStartProcessRejected,
} from '@/store/selectors/start-process';
import {
  selectActiveProcesses,
  selectIsActiveProcessesPending,
  selectIsActiveProcessesRejected,
} from '@/store/selectors/active-processes';
import {
  selectFinishedProcesses,
  selectIsFinishedProcessesPending,
  selectIsFinishedProcessesRejected,
  selectIsFinishedProcessesMinorPending,
  selectFinishedProcessesTotal,
} from '@/store/selectors/finished-processes';
import {
  selectFiltersSortByColumn,
  selectFiltersQueries,
  selectFiltersLabels,
} from '@/store/selectors/filters';
import { selectIsUserManagerOrAdmin, selectIsUserAdmin } from '@/store/selectors/user';
import Sidebar from '@/components/common/Sidebar';
import LogoutRow from '@/components/common/LogoutRow';
import Modal from '@/components/common/Modal';
import AvailableProcess from '@/components/Processes/AvailableProcesses';
import StartProcessModal from '@/components/Processes/StartProcessModal';
import ScheduledProcesses from '@/components/Processes/ScheduledProcesses';
import ActiveProcesses from '@/components/Processes/ActiveProcesses';
import FinishedProcesses from '@/components/Processes/FinishedProcesses';
import ClearFilters from '@/components/Processes/FinishedProcesses/ClearFilters';
import { DaysOfWeek as DaysOfWeekEnum } from '@/@types/days-of-week';
import Filters from './Filters';

const Processes: React.FC = () => {
  const dispatch = useDispatch();

  const availableProcesses = useSelector(selectAvailableProcesses);
  const isAvailableProcessesPending = useSelector(selectIsAvailableProcessesPending);
  const isAvailableProcessesRejected = useSelector(selectIsAvailableProcessesRejected);

  const scheduledProcesses = useSelector(selectScheduledProcesses);
  const isScheduledProcessesPending = useSelector(selectIsScheduledProcessesPending);
  const isScheduledProcessesRejected = useSelector(selectIsScheduledProcessesRejected);

  const regularProcesses = useSelector(selectRegularProcesses);
  // const isRegularProcessesPending = useSelector(selectIsRegularProcessesPending);
  // const isRegularProcessesRejected = useSelector(selectIsRegularProcessesRejected);

  const startProcess = useSelector(selectIsStartProcess);
  const isStartProcessPending = useSelector(selectIsStartProcessPending);
  const isStartProcessRejected = useSelector(selectIsStartProcessRejected);

  const activeProcesses = useSelector(selectActiveProcesses);
  const isActiveProcessesPending = useSelector(selectIsActiveProcessesPending);
  const isActiveProcessesRejected = useSelector(selectIsActiveProcessesRejected);

  const finishedProcesses = useSelector(selectFinishedProcesses);
  const isFinishedProcessesPending = useSelector(selectIsFinishedProcessesPending);
  const isFinishedProcessesRejected = useSelector(selectIsFinishedProcessesRejected);
  const isFinishedProcessesMinorPending = useSelector(selectIsFinishedProcessesMinorPending);
  const finishedProcessesTotal = useSelector(selectFinishedProcessesTotal);

  const sortByColumn = useSelector(selectFiltersSortByColumn);
  const finishedFiltersQueries = useSelector(selectFiltersQueries);
  const filtersLabels = useSelector(selectFiltersLabels);

  const isUserManagerOrAdmin = useSelector(selectIsUserManagerOrAdmin);
  const isUserAdmin = useSelector(selectIsUserAdmin);

  useEffect(() => {
    dispatch(loadAvailableProcesses());
    dispatch(loadScheduledProcesses());
    dispatch(loadRegularProcesses());
    dispatch(loadActiveProcesses());
    dispatch(loadFinishedProcesses());
    dispatch(loadFilters());
  }, []);

  const handleTryReloadAvailableProcesses = () => dispatch(loadAvailableProcesses());
  const handleTryReloadScheduledAndRegularProcesses = () => {
    dispatch(loadScheduledProcesses());
    dispatch(loadRegularProcesses());
  };
  const handleTryReloadActiveProcesses = () => dispatch(loadActiveProcesses());
  const handleTryReloadFinishedProcesses = () => dispatch(loadFinishedProcesses());

  const handleStartProcessClick = (id: number) => () => {
    dispatch(setProcessAsync(id));
  };

  const handleModalClose = () => {
    if (isStartProcessPending) return;

    dispatch(startProcessActions.reset());
  };

  const handleModalSubmit = (properties: IPropertyWithValue[], timestamp: string | undefined) => {
    dispatch(timestamp
      ? scheduleProcessAsync(timestamp, properties)
      : startProcessAsync(properties));
  };

  const handleRegularProcessSubmit = (
    properties: IPropertyWithValue[],
    selectedRegularDaysOfWeek: Array<DaysOfWeekEnum>,
    selectedRegularTime: string,
  ) => {
    dispatch(createRegularProcessAsync(properties, selectedRegularDaysOfWeek, selectedRegularTime));
  };

  const handlePageChange = (page: number) => {
    if (isFinishedProcessesMinorPending || isFinishedProcessesPending) return;

    dispatch(changePageAsync(page));
  };

  const handleSortByChange = (sortBy: SortsFields) => {
    if (isFinishedProcessesMinorPending || isFinishedProcessesPending) return;

    dispatch(changeSortByAsync(sortBy));
  };

  const clearFilters = () => {
    dispatch(clearFiltersAsync());
  };

  return (
    <>
      <Helmet>
        <title>Processes</title>
      </Helmet>

      <ProcessesWrapperStyled>
        <Sidebar />

        <ProcessesContentStyled>
          <LogoutRow />

          <AvailableProcess
            onStartProcessClick={handleStartProcessClick}
            processes={availableProcesses}
            isLoading={isAvailableProcessesPending}
            isError={isAvailableProcessesRejected}
            handleTryReload={handleTryReloadAvailableProcesses}
          />

          <ScheduledProcesses
            processes={scheduledProcesses}
            regularProcesses={regularProcesses}
            isLoading={isScheduledProcessesPending}
            isError={isScheduledProcessesRejected}
            isUserManagerOrAdmin={isUserManagerOrAdmin}
            handleTryReload={handleTryReloadScheduledAndRegularProcesses}
          />

          <ActiveProcesses
            processes={activeProcesses}
            isLoading={isActiveProcessesPending}
            isError={isActiveProcessesRejected}
            isUserManagerOrAdmin={isUserManagerOrAdmin}
            handleTryReload={handleTryReloadActiveProcesses}
          />

          <FinishedProcesses
            handleTryReload={handleTryReloadFinishedProcesses}
            processes={finishedProcesses}
            isLoading={isFinishedProcessesPending}
            isError={isFinishedProcessesRejected}
            isUserManagerOrAdmin={isUserManagerOrAdmin}
            isUserAdmin={isUserAdmin}
            isFinishedProcessesMinorPending={isFinishedProcessesMinorPending}
            finishedProcessesTotal={finishedProcessesTotal}
            finishedFiltersQueries={finishedFiltersQueries}
            handlePageChange={handlePageChange}
            handleSortByChange={handleSortByChange}
            sortByColumn={sortByColumn}
            clearFilters={<ClearFilters onClick={clearFilters} isHide={!filtersLabels.length} />}
            filters={<Filters />}
          />
        </ProcessesContentStyled>
      </ProcessesWrapperStyled>

      {startProcess && (
        <Modal onBackdropClick={handleModalClose}>
          <StartProcessModal
            handleCancel={handleModalClose}
            handleSubmit={handleModalSubmit}
            handleRegularProcessSubmit={handleRegularProcessSubmit}
            process={startProcess}
            isPending={isStartProcessPending}
            isRejected={isStartProcessRejected}
          />
        </Modal>
      )}
    </>
  );
};

const ProcessesWrapperStyled = styled.div`
  display: flex;
  min-height: 100vh;
`;

const ProcessesContentStyled = styled.div`
  width: calc(100% - 72px);
  padding: 0px 25px;
`;

export default Processes;
