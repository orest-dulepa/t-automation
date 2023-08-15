export enum FiltersFields {
  processes = 'processes_filter',
  statuses = 'statuses_filter',
  inputs = 'inputs_filter',
  endTimes = 'end_times_filter',
  executedBy = 'executed_by_filter'
}

export interface IQueryFilters {
  [FiltersFields.processes]?: string;
  [FiltersFields.statuses]?: string;
  [FiltersFields.inputs]?: string;
  [FiltersFields.executedBy]?: string;
  [FiltersFields.endTimes]?: string;
}

export enum PaginationFields {
  page = 'page',
  amount = 'amount'
}

export interface IQueryPagination {
  [PaginationFields.page]: number;
  [PaginationFields.amount]: number;
}

export enum SortsFields {
  processes = 'processes_sort',
  runNumber = 'run_number_sort',
  duration = 'duration_sort',
  endTimes = 'end_times_sort',
  executedBy = 'executed_by_sort'
}

export interface IQuerySorts {
  [SortsFields.processes]?: 1 | 0;
  [SortsFields.runNumber]?: 1 | 0;
  [SortsFields.duration]?: 1 | 0;
  [SortsFields.endTimes]?: 1 | 0;
  [SortsFields.executedBy]?: 1 | 0;
}

export interface IQueries extends IQueryFilters, IQueryPagination, IQuerySorts {}
