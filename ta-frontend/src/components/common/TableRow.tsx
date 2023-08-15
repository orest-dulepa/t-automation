import React from 'react';
import { useHistory } from 'react-router-dom';
import styled from 'styled-components';

interface IProps {
  id: number;
}

const TableRow: React.FC<IProps> = ({ children, id }) => {
  const history = useHistory();

  const handleClick = () => {
    history.push(`/processes/${id}`);
  };

  return <TableRowStyled onClick={handleClick}>{children}</TableRowStyled>;
};

const TableRowStyled = styled.tr`
  cursor: pointer;

  &:hover td {
    background-color: rgba(241, 242, 246, 0.25);
    transition: 0.15s;
  }

  & td {
    &:last-child {
      position: relative;
      padding-right: 40px;

      &:after {
        content: '';
        display: block;
        position: absolute;
        top: 49%;
        right: 15px;
        width: 15px;
        height: 15px;
        transform: translateY(-50%);
        background-image: url('/assets/arrow-point-to-right.svg');
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
      }
    }
  }
`;

export default TableRow;
