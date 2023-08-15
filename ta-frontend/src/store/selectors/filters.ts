import { createSelector, Selector } from 'reselect';
import moment from 'moment';

import { IProcess } from '@/interfaces/process';
import { IQueries, FiltersFields, SortsFields } from '@/interfaces/filter';
import { IUser } from '@/interfaces/user';

import { State } from '@/store';

import { neverReached } from '@/utils/never-reached';

const selectFiltersState = (state: State) => state.filtersReducer;

export const selectIsFiltersPending: Selector<State, boolean> = createSelector(
  selectFiltersState,
  ({ isPending }) => isPending,
);

export const selectIsFiltersRejected: Selector<State, boolean> = createSelector(
  selectFiltersState,
  ({ isRejected }) => isRejected,
);

export const selectFiltersProcesses: Selector<State, IProcess[]> = createSelector(
  selectFiltersState,
  ({ processes }) => processes,
);

export const selectFiltersUsers: Selector<State, IUser[]> = createSelector(
  selectFiltersState,
  ({ users }) => users,
);

export const selectFiltersQueries: Selector<State, IQueries> = createSelector(
  selectFiltersState,
  ({ queries }) => queries,
);

export const selectFiltersSortByColumn: Selector<
State,
{ column: SortsFields; order: 1 | 0 }
> = createSelector(selectFiltersState, ({ queries }) => {
  switch (true) {
    case queries[SortsFields.processes] !== undefined: {
      return { column: SortsFields.processes, order: queries[SortsFields.processes] as 1 | 0 };
    }
    case queries[SortsFields.runNumber] !== undefined: {
      return { column: SortsFields.runNumber, order: queries[SortsFields.runNumber] as 1 | 0 };
    }
    case queries[SortsFields.duration] !== undefined: {
      return { column: SortsFields.duration, order: queries[SortsFields.duration] as 1 | 0 };
    }
    case queries[SortsFields.endTimes] !== undefined: {
      return { column: SortsFields.endTimes, order: queries[SortsFields.endTimes] as 1 | 0 };
    }
    case queries[SortsFields.executedBy] !== undefined: {
      return { column: SortsFields.executedBy, order: queries[SortsFields.executedBy] as 1 | 0 };
    }
    default: {
      return undefined as any;
    }
  }
});

export const selectFiltersLabels: Selector<
State,
{ title: string; filter: FiltersFields; value: string }[]
> = createSelector(selectFiltersState, ({ users, processes, labels }) => (
  labels.map((label) => {
    const [filter, value] = label;

    switch (filter) {
      case FiltersFields.processes: {
        const { name } = processes.find(({ id }) => id === Number(value))!;

        return {
          title: name,
          filter,
          value,
        };
      }
      case FiltersFields.statuses: {
        return {
          title: value === 'finished' ? 'Success' : 'Failed',
          filter,
          value,
        };
      }
      case FiltersFields.inputs: {
        return {
          title: `Input: ${value}`,
          filter,
          value,
        };
      }
      case FiltersFields.endTimes: {
        const values = value.split('-');

        let title = '';
        const format = 'YYYY-MM-DD';

        if (values.length === 2) {
          const [from, to] = values;

          const fromFormatted = moment(Number(from)).format(format);
          const toFormatted = moment(Number(to)).format(format);

          title = `${fromFormatted}...${toFormatted}`;
        } else {
          const [day] = values;

          const dayFormatted = moment(Number(day)).format(format);

          title = dayFormatted;
        }

        return {
          title,
          filter,
          value,
        };
      }
      case FiltersFields.executedBy: {
        const user = users.find(({ id }) => id === Number(value))!;

        return {
          title: user.email,
          filter,
          value,
        };
      }
      default: {
        neverReached(filter);

        return undefined as any;
      }
    }
  })));
