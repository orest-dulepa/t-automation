import React from 'react';
import styled from 'styled-components';

const TableHead: React.FC = ({ children }) => <TableHeadStyled>{children}</TableHeadStyled>;

const TableHeadStyled = styled.thead`
  background-color: #f1f2f6;
  text-transform: uppercase;
  font-weight: 500;
  font-size: 12px;

  th {
    background-color: #f1f2f6;
    border-color: #f1f2f6;
    padding: 10px;
    color: #83839c;
    white-space: nowrap;
    text-align: left;
  }
`;

export default TableHead;
