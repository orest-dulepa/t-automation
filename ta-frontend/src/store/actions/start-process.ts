import { createActionCreators } from 'immer-reducer';
import { IPropertyWithValue } from '@/interfaces/process';
import { StartProcessReducer } from '@/store/reducers/start-process';
import { DaysOfWeek as DaysOfWeekEnum } from '@/@types/days-of-week';
import { localToUTC } from '@/utils/time';
import { AsyncAction } from './common';
import { loadActiveProcesses } from './active-processes';
import { loadRegularProcesses, loadScheduledProcesses } from './scheduled-processes';

export const startProcessActions = createActionCreators(StartProcessReducer);

export type StartProcessActions =
  | ReturnType<typeof startProcessActions.setIsPending>
  | ReturnType<typeof startProcessActions.setIsRejected>
  | ReturnType<typeof startProcessActions.setProcess>;

export const setProcessAsync = (id: number): AsyncAction => (dispatch, getState) => {
  try {
    const { availableProcessesReducer } = getState();
    const { processes } = availableProcessesReducer;

    const foundProcess = processes.find((process) => process.id === id);

    dispatch(startProcessActions.setProcess(foundProcess!));
  } catch (e) {
    console.log(e);
  }
};

export const startProcessAsync = (properties: IPropertyWithValue[]): AsyncAction => async (
  dispatch,
  getState,
  { mainApiProtected },
) => {
  try {
    dispatch(startProcessActions.setIsPending());

    const { startProcessReducer, activeProcessesReducer } = getState();

    const { id } = startProcessReducer.process!;
    const { processes } = activeProcessesReducer;

    await mainApiProtected.startProcess(id, properties);

    dispatch(startProcessActions.reset());

    if (!processes.length) {
      dispatch(loadActiveProcesses());
    }
  } catch (e) {
    console.log(e);

    dispatch(startProcessActions.setIsRejected());
  }
};

export const createRegularProcessAsync = (
  properties: IPropertyWithValue[],
  selectedRegularDaysOfWeek: Array<DaysOfWeekEnum>,
  selectedRegularTime: string,
): AsyncAction => async (
  dispatch,
  getState,
  { mainApiProtected },
) => {
  try {
    dispatch(startProcessActions.setIsPending());

    const { startProcessReducer, regularProcessesReducer } = getState();

    const { id } = startProcessReducer.process!;
    const { processes } = regularProcessesReducer;

    const body = {
      processId: id,
      meta: properties,
      daysOfWeek: selectedRegularDaysOfWeek,
      startTime: localToUTC(selectedRegularTime),
    };

    await mainApiProtected.createRegularProcess(body);

    dispatch(startProcessActions.reset());

    if (!processes.length) {
      dispatch(loadRegularProcesses());
    }
  } catch (e) {
    console.log(e);

    dispatch(startProcessActions.setIsRejected());
  }
};

export const scheduleProcessAsync = (
  timestamp: string, meta: IPropertyWithValue[],
): AsyncAction => async (
  dispatch,
  getState,
  { mainApiProtected },
) => {
  try {
    dispatch(startProcessActions.setIsPending());

    const { startProcessReducer, scheduledProcessesReducer } = getState();

    const { id } = startProcessReducer.process!;
    const { processes } = scheduledProcessesReducer;

    await mainApiProtected.scheduleProcess(id, { timestamp, meta });

    dispatch(startProcessActions.reset());

    if (!processes.length) {
      dispatch(loadScheduledProcesses());
    }
  } catch (e) {
    console.log(e);

    dispatch(startProcessActions.setIsRejected());
  }
};
