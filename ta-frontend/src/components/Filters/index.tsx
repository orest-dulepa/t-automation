import React from 'react';
import styled from 'styled-components';

import { IQueries, FiltersFields } from '@/interfaces/filter';
import { IProcess } from '@/interfaces/process';
import { IUser } from '@/interfaces/user';

import FiltersRow from './FiltersRow';
import FiltersLabelsRow from './FiltersLabelsRow';
import ItemsPerPage from './ItemsPerPage';

interface IProps {
  finishedFiltersQuery: IQueries;
  handleAmountChange: (amount: number) => void;
  finishedFiltersProcesses: IProcess[];
  addFilter: (query: FiltersFields) => (value: number | string) => void;
  finishedFiltersUsers: IUser[];
  isUserManagerOrAdmin: boolean;
  filtersLabels: { title: string; filter: FiltersFields; value: string }[];
  removeFilter: (query: FiltersFields, value: number | string) => void;
  isFinishedFiltersPending: boolean;
  isFinishedFiltersRejected: boolean;
}

const Filters: React.FC<IProps> = ({
  finishedFiltersQuery,
  handleAmountChange,
  finishedFiltersProcesses,
  addFilter,
  finishedFiltersUsers,
  isUserManagerOrAdmin,
  filtersLabels,
  removeFilter,
  isFinishedFiltersPending,
  isFinishedFiltersRejected,
}) => (
  <FiltersStyled>
    <FiltersSectionStyled>
      {!isFinishedFiltersPending && !isFinishedFiltersRejected && (
        <>
          <FiltersRow
            finishedFiltersProcesses={finishedFiltersProcesses}
            addFilter={addFilter}
            finishedFiltersUsers={finishedFiltersUsers}
            isUserManagerOrAdmin={isUserManagerOrAdmin}
          />
          <FiltersLabelsRow filtersLabels={filtersLabels} removeFilter={removeFilter} />
        </>
      )}
    </FiltersSectionStyled>
    <ItemsSectionStyled>
      <ItemsPerPage
        currentItemsPerPage={finishedFiltersQuery.amount}
        onChange={handleAmountChange}
      />
    </ItemsSectionStyled>
  </FiltersStyled>
);

const FiltersStyled = styled.div`
  display: flex;
  padding-bottom: 15px;
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
