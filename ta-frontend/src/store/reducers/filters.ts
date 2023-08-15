import { createReducerFunction, ImmerReducer } from 'immer-reducer';

import { IProcess } from '@/interfaces/process';
import { IUser } from '@/interfaces/user';
import {
  IQueries,
  FiltersFields,
  PaginationFields,
  SortsFields,
} from '@/interfaces/filter';

export interface IFiltersState {
  isPending: boolean;
  isRejected: boolean;
  processes: IProcess[];
  users: IUser[];
  labels: [FiltersFields, string][];
  queries: IQueries;
}

const initialState: IFiltersState = {
  isPending: false,
  isRejected: false,
  processes: [],
  users: [],
  labels: [],
  queries: {
    [FiltersFields.processes]: undefined,
    [FiltersFields.statuses]: undefined,
    [FiltersFields.inputs]: undefined,
    [FiltersFields.endTimes]: undefined,
    [FiltersFields.executedBy]: undefined,
    [SortsFields.processes]: undefined,
    [SortsFields.runNumber]: undefined,
    [SortsFields.duration]: undefined,
    [SortsFields.endTimes]: 1,
    [SortsFields.executedBy]: undefined,
    [PaginationFields.amount]: 10,
    [PaginationFields.page]: 1,
  },
};

export class FiltersReducer extends ImmerReducer<IFiltersState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setProcessesAndUsers(processes: IProcess[], users: IUser[]) {
    this.draftState.isPending = false;
    this.draftState.processes = processes;
    this.draftState.users = users;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }

  public setAmount(amount: number) {
    this.draftState.queries[PaginationFields.amount] = amount;
  }

  public setPage(page: number) {
    this.draftState.queries[PaginationFields.page] = page;
  }

  public setSortBy(sortBy: SortsFields) {
    if (typeof this.draftState.queries[sortBy] === 'number') {
      this.draftState.queries[sortBy] = Number(!this.draftState.queries[sortBy]) as 1 | 0;
      return;
    }

    const resetSortFields: { [key in SortsFields]: undefined } = {
      [SortsFields.processes]: undefined,
      [SortsFields.runNumber]: undefined,
      [SortsFields.duration]: undefined,
      [SortsFields.endTimes]: undefined,
      [SortsFields.executedBy]: undefined,
    };

    this.draftState.queries = { ...this.draftState.queries, ...resetSortFields };

    this.draftState.queries[sortBy] = 1;
  }

  public setFilter(query: FiltersFields, value: string | undefined) {
    this.draftState.queries[query] = value;
  }

  public setLabels(labels: [FiltersFields, string][]) {
    this.draftState.labels = labels;
  }

  public clearFilters() {
    const resetFiltersFields: { [key in FiltersFields]: undefined } = {
      [FiltersFields.processes]: undefined,
      [FiltersFields.statuses]: undefined,
      [FiltersFields.inputs]: undefined,
      [FiltersFields.endTimes]: undefined,
      [FiltersFields.executedBy]: undefined,
    };

    this.draftState.queries = { ...this.draftState.queries, ...resetFiltersFields };
    this.draftState.labels = [];
  }
}

export default createReducerFunction(FiltersReducer, initialState);
