import React, { useMemo } from 'react';
import styled from 'styled-components';

import { IQueries } from '@/interfaces/filter';

const trimPages = (pages: number[], currentPage: number) => {
  if (pages.length <= 7) return pages;

  if (currentPage <= 3) return [...pages.slice(0, 5), '...', pages.length];

  if (currentPage >= pages.length - 3) return [pages[0], '...', ...pages.slice(pages.length - 5)];

  return [pages[0], '...', ...pages.slice(currentPage - 2, currentPage + 1), '...', pages.length];
};

interface IProps {
  handlePageChange: (page: number) => void;
  finishedProcessesTotal: number;
  finishedFiltersQueries: IQueries;
}

const Pagination: React.FC<IProps> = ({
  handlePageChange,
  finishedProcessesTotal,
  finishedFiltersQueries,
}) => {
  const handlePageClick = (page: number) => () => {
    handlePageChange(page);
  };

  const { amount: itemsPerPage, page: currentPage } = finishedFiltersQueries;

  const totalPagesAmount = useMemo(() => Math.ceil(finishedProcessesTotal / itemsPerPage), [
    finishedProcessesTotal,
    itemsPerPage,
  ]);

  const pages = useMemo(() => Array.from({ length: totalPagesAmount }, (_, i) => i + 1), [
    totalPagesAmount,
  ]);

  const trimmedPages = useMemo(() => trimPages(pages, currentPage), [pages, currentPage]);

  if (!finishedProcessesTotal) return null;

  return (
    <PaginationStyled>
      <DirectionButtonLeft
        onClick={handlePageClick(currentPage - 1)}
        disabled={currentPage === 1}
      />
      {trimmedPages.map((page, i) => (
        <PageButton
          onClick={typeof page === 'number' ? handlePageClick(Number(page)) : undefined}
          key={i}
          isActive={page === currentPage}
        >
          {page}
        </PageButton>
      ))}
      <DirectionButtonRight
        onClick={handlePageClick(currentPage + 1)}
        disabled={currentPage === totalPagesAmount}
      />
    </PaginationStyled>
  );
};

const PaginationStyled = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0px 0px 25px 0px;
`;

const DirectionButtonLeft = styled.button`
  width: 24px;
  height: 24px;
  font-size: 30px;
  color: #8b88a2;
  cursor: pointer;
  background-image: url('/assets/chevron.svg');
  background-position: center;
  background-size: contain;
  background-repeat: no-repeat;
  background-color: transparent;
  outline: none;
  border: none;

  &:disabled {
    cursor: not-allowed;
  }
`;

const DirectionButtonRight = styled(DirectionButtonLeft)`
  transform: rotate(180deg);
`;

const PageButton = styled.div<{ isActive: boolean }>`
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-weight: 500;
  font-size: 16px;
  color: #8b88a2;
  border: 1px solid transparent;
  border-radius: 4px;
  background-color: ${({ isActive }) => (isActive ? 'white' : 'transparent')};
  border-color: ${({ isActive }) => (isActive ? '#F1F2F6' : 'transparent')};
`;

export default Pagination;
