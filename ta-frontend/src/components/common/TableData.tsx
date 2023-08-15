import React from 'react';
import styled from 'styled-components';

interface IProps extends React.TdHTMLAttributes<HTMLTableDataCellElement> {}

const TableData: React.FC<IProps> = (props) => <TableDataStyled {...props} />;

const TableDataStyled = styled.td`
  background-color: #ffffff;
  border-top: 1px solid #f1f2f6;
  vertical-align: middle;
  font-size: 16px;
  padding: 12px;
`;

export default TableData;
