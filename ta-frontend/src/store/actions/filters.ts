import { createActionCreators } from 'immer-reducer';
import xor from 'lodash/xor';

import { FiltersReducer } from '@/store/reducers/filters';

import { SortsFields, FiltersFields } from '@/interfaces/filter';

import { AsyncAction } from './common';
import { loadFinishedProcessesViaFilters } from './finished-processes';

export const filtersActions = createActionCreators(FiltersReducer);

export type FiltersActions =
  | ReturnType<typeof filtersActions.setIsPending>
  | ReturnType<typeof filtersActions.setIsRejected>
  | ReturnType<typeof filtersActions.setProcessesAndUsers>
  | ReturnType<typeof filtersActions.setAmount>
  | ReturnType<typeof filtersActions.setPage>
  | ReturnType<typeof filtersActions.setSortBy>
  | ReturnType<typeof filtersActions.setFilter>
  | ReturnType<typeof filtersActions.clearFilters>
  | ReturnType<typeof filtersActions.setLabels>;

export const loadFilters = (): AsyncAction => async (dispatch, _, { mainApiProtected }) => {
  try {
    dispatch(filtersActions.setIsPending());

    const { processes, users } = await mainApiProtected.getFinishedProcessesFilters();

    dispatch(filtersActions.setProcessesAndUsers(processes, users));
  } catch (e) {
    dispatch(filtersActions.setIsRejected());
  }
};

export const changeAmountAsync = (amount: number): AsyncAction => async (dispatch) => {
  dispatch(filtersActions.setAmount(amount));
  dispatch(filtersActions.setPage(1));

  dispatch(loadFinishedProcessesViaFilters());
};

export const changePageAsync = (page: number): AsyncAction => async (dispatch) => {
  dispatch(filtersActions.setPage(page));

  dispatch(loadFinishedProcessesViaFilters());
};

export const changeSortByAsync = (sortBy: SortsFields): AsyncAction => async (dispatch) => {
  dispatch(filtersActions.setSortBy(sortBy));

  dispatch(loadFinishedProcessesViaFilters());
};

export const addFilterAsync = (queryField: FiltersFields, value: string): AsyncAction => async (
  dispatch,
  getState,
) => {
  const { filtersReducer } = getState();
  const { queries, labels } = filtersReducer;

  const labelsCopy = [...labels];
  const query = queries[queryField];
  const values = query?.split(';') || [];

  if (values.includes(value)) return;

  const newLabel = [queryField, value] as [FiltersFields, string];

  values.push(value);
  labelsCopy.push(newLabel);

  const valueToSave = values.join(';');

  dispatch(filtersActions.setPage(1));
  dispatch(filtersActions.setFilter(queryField, valueToSave));
  dispatch(filtersActions.setLabels(labelsCopy));

  dispatch(loadFinishedProcessesViaFilters());
};

export const removeFilterAsync = (queryField: FiltersFields, value: string): AsyncAction => async (
  dispatch,
  getState,
) => {
  const { filtersReducer } = getState();
  const { queries, labels } = filtersReducer;

  const query = queries[queryField];
  const values = query?.split(';') || [];

  if (!values.includes(value)) return;

  const newLabel = [queryField, value] as [FiltersFields, string];

  const filteredValues = values.filter((fieldValue) => fieldValue !== value);
  const filteredLabels = labels.filter((label) => xor(newLabel, label).length !== 0);

  const valueToSave = filteredValues.length ? filteredValues.join(';') : undefined;

  dispatch(filtersActions.setPage(1));
  dispatch(filtersActions.setFilter(queryField, valueToSave));
  dispatch(filtersActions.setLabels(filteredLabels));

  dispatch(loadFinishedProcessesViaFilters());
};

export const clearFiltersAsync = (): AsyncAction => async (dispatch) => {
  dispatch(filtersActions.clearFilters());
  dispatch(filtersActions.setPage(1));

  dispatch(loadFinishedProcessesViaFilters());
};
