import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import styled from 'styled-components';

import { FiltersFields } from '@/interfaces/filter';

import { changeAmountAsync, addFilterAsync, removeFilterAsync } from '@/store/actions/filters';

import { selectIsFinishedProcessesPending, selectIsFinishedProcessesMinorPending } from '@/store/selectors/finished-processes';
import {
  selectIsFiltersPending,
  selectIsFiltersRejected,
  selectFiltersQueries,
  selectFiltersProcesses,
  selectFiltersUsers,
  selectFiltersLabels,
} from '@/store/selectors/filters';
import { selectIsUserManagerOrAdmin } from '@/store/selectors/user';

import FiltersRow from '@/components/Filters/FiltersRow';
import FiltersLabelsRow from '@/components/Filters/FiltersLabelsRow';
import ItemsPerPage from '@/components/Filters/ItemsPerPage';

const Filters: React.FC = () => {
  const isFinishedProcessesPending = useSelector(selectIsFinishedProcessesPending);
  const isFinishedProcessesMinorPending = useSelector(selectIsFinishedProcessesMinorPending);

  const isFinishedFiltersPending = useSelector(selectIsFiltersPending);
  const isFinishedFiltersRejected = useSelector(selectIsFiltersRejected);
  const finishedFiltersQuery = useSelector(selectFiltersQueries);
  const finishedFiltersProcesses = useSelector(selectFiltersProcesses);
  const finishedFiltersUsers = useSelector(selectFiltersUsers);
  const filtersLabels = useSelector(selectFiltersLabels);

  const isUserManagerOrAdmin = useSelector(selectIsUserManagerOrAdmin);

  const dispatch = useDispatch();

  const handleAmountChange = (amount: number) => {
    dispatch(changeAmountAsync(amount));
  };

  const addFilter = (query: FiltersFields) => (value: string) => {
    if (isFinishedProcessesPending || isFinishedProcessesMinorPending) return;

    dispatch(addFilterAsync(query, value));
  };

  const removeFilter = (query: FiltersFields, value: string) => {
    if (isFinishedProcessesPending || isFinishedProcessesMinorPending) return;

    dispatch(removeFilterAsync(query, value));
  };

  if (isFinishedFiltersPending || isFinishedFiltersRejected) return null;

  return (
    <FiltersStyled>
      <FiltersSectionStyled>
        <FiltersRow
          finishedFiltersProcesses={finishedFiltersProcesses}
          addFilter={addFilter}
          finishedFiltersUsers={finishedFiltersUsers}
          isUserManagerOrAdmin={isUserManagerOrAdmin}
        />
        <FiltersLabelsRow filtersLabels={filtersLabels} removeFilter={removeFilter} />
      </FiltersSectionStyled>
      <ItemsSectionStyled>
        <ItemsPerPage
          currentItemsPerPage={finishedFiltersQuery.amount}
          onChange={handleAmountChange}
        />
      </ItemsSectionStyled>
    </FiltersStyled>
  );
};

const FiltersStyled = styled.div`
  display: flex;
  padding-bottom: 20px;
`;

const FiltersSectionStyled = styled.div`
  width: 100%;
`;

const ItemsSectionStyled = styled.div`
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  min-width: 300px;
`;

export default Filters;
