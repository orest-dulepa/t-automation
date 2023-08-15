import React, { useEffect, useState } from 'react';
import styled from 'styled-components';

interface IProps {
  list: Array<any>;
  setCurrentList: React.Dispatch<React.SetStateAction<any>>
}

const Pagination: React.FC<IProps> = ({ list, setCurrentList }) => {
  const perPage = 3;
  const [currentPage, setCurrentPage] = useState(0);
  const [lastPage, setLastPage] = useState(0);
  const [itemsInfo, setItemsInfo] = useState('1-3');

  useEffect(() => {
    setLastPage(Math.ceil(list.length / perPage) - 1);
    updateList();
  }, [list.length]);

  useEffect(() => {
    updateList();
  }, [currentPage]);

  const updateList = () => {
    const indexOfFirstTodo = currentPage * perPage;
    const indexOfLastTodo = indexOfFirstTodo + perPage;
    const curList = list.slice(indexOfFirstTodo, indexOfLastTodo);
    setCurrentList(curList);
    setItemsInfo(`${indexOfFirstTodo + 1} - ${indexOfFirstTodo + curList.length}`);
  };

  const handlePrevPageClick = () => {
    setCurrentPage(currentPage - 1);
  };

  const handlePrevNextClick = () => {
    setCurrentPage(currentPage + 1);
  };

  return (
    <PaginationStyled>
      <PagesStyled>
        {itemsInfo}
        {' '}
        of
        {' '}
        {list.length}
      </PagesStyled>
      <ButtonStyled disabled={currentPage === 0} onClick={handlePrevPageClick}>
        ‹
      </ButtonStyled>
      <ButtonStyled disabled={currentPage === lastPage} onClick={handlePrevNextClick}>
        ›
      </ButtonStyled>
    </PaginationStyled>
  );
};

const PaginationStyled = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 15px;
  background-color: white;
  border-left: 1px solid #f1f2f6;
  border-right: 1px solid #f1f2f6;
  border-bottom: 1px solid #f1f2f6;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
`;

const PagesStyled = styled.div`
  color: #afafc6;
  font-size: 16px;
`;

const ButtonStyled = styled.button`
  width: 30px;
  height: 30px;
  color: #83839c;
  border: 1px solid #ebedf2;
  border-radius: 6px;
  cursor: pointer;
  outline: none;
  background-color: white;
  margin-left: 18px;

  &:disabled {
    cursor: not-allowed;
    border: 1px solid #ebedf2;
    color: #ebedf2;
  }
`;

export default Pagination;
