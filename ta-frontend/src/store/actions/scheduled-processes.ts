import xor from 'lodash/xor';
import { createActionCreators } from 'immer-reducer';
import { IScheduledProcess } from '@/interfaces/scheduled-process';
import { sleep } from '@/utils/sleep';
import { ScheduledProcessesReducer } from '@/store/reducers/scheduled-processes';
import { RegularProcessesReducer } from '@/store/reducers/regular-processes';
import { IRegularProcess } from '@/interfaces/regular-process';
import { AsyncAction } from './common';
import { loadActiveProcesses } from './active-processes';

export const scheduledProcessesActions = createActionCreators(ScheduledProcessesReducer);
export const regularProcessesActions = createActionCreators(RegularProcessesReducer);

export type ScheduledProcessesActions =
  | ReturnType<typeof scheduledProcessesActions.setIsPending>
  | ReturnType<typeof scheduledProcessesActions.setProcesses>
  | ReturnType<typeof scheduledProcessesActions.setIsRejected>;

export type RegularProcessesActions =
  | ReturnType<typeof regularProcessesActions.setIsPending>
  | ReturnType<typeof regularProcessesActions.setProcesses>
  | ReturnType<typeof regularProcessesActions.setIsRejected>;

export const loadScheduledProcesses = (): AsyncAction => async (
  dispatch, _, { mainApiProtected },
) => {
  try {
    dispatch(scheduledProcessesActions.setIsPending());

    const processes = await mainApiProtected.getScheduledProcesses();

    dispatch(scheduledProcessesActions.setProcesses(processes));

    if (processes.length) {
      dispatch(processesMonitor());
    }
  } catch (e) {
    dispatch(scheduledProcessesActions.setIsRejected());
  }
};

export const loadRegularProcesses = (): AsyncAction => async (
  dispatch, _, { mainApiProtected },
) => {
  try {
    dispatch(regularProcessesActions.setIsPending());

    const processes = await mainApiProtected.getRegularProcesses();

    dispatch(regularProcessesActions.setProcesses(processes));

    if (processes.length) {
      dispatch(processesMonitor());
    }
  } catch (e) {
    dispatch(regularProcessesActions.setIsRejected());
  }
};

const processesMonitor = (): AsyncAction => async (dispatch, getState, { mainApiProtected }) => {
  try {
    const { router, scheduledProcessesReducer, regularProcessesReducer } = getState();
    const { pathname } = router.location;

    if (pathname !== '/processes') return;

    const scheduledProcessesFromRequest = await mainApiProtected.getScheduledProcesses();
    const regularProcessesFromRequest = await mainApiProtected.getRegularProcesses();

    const { processes: scheduledProcessesFromStore } = scheduledProcessesReducer;
    const { processes: regularProcessesFromStore } = regularProcessesReducer;

    const getScheduledId = ({ id }: IScheduledProcess) => id;
    const getRegularId = ({ id }: IRegularProcess) => id;

    const scheduledProcessesRunIdFromRequest = scheduledProcessesFromRequest.map(getScheduledId);
    const regularProcessesRunIdFromRequest = regularProcessesFromRequest.map(getRegularId);
    const scheduledProcessesRunIdFromStore = scheduledProcessesFromStore.map(getScheduledId);
    const regularProcessesRunIdFromStore = regularProcessesFromStore.map(getRegularId);

    const scheduledDifference = xor(
      scheduledProcessesRunIdFromRequest, scheduledProcessesRunIdFromStore,
    );
    const regularDifference = xor(regularProcessesRunIdFromRequest, regularProcessesRunIdFromStore);

    await sleep(2500);

    dispatch(scheduledProcessesActions.setProcesses(scheduledProcessesFromRequest));
    dispatch(regularProcessesActions.setProcesses(regularProcessesFromRequest));

    if (scheduledDifference.length || regularDifference.length) {
      dispatch(loadScheduledProcesses());
      dispatch(loadRegularProcesses());
      dispatch(loadActiveProcesses());
      return;
    }

    dispatch(processesMonitor());
  } catch (e) {
    console.log(e);
  }
};
