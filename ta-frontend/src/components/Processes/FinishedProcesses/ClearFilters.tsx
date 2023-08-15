import React from 'react';
import styled from 'styled-components';

interface IProps {
  onClick: () => void;
  isHide: boolean;
}

const ClearFilters: React.FC<IProps> = ({ onClick, isHide }) => {
  if (isHide) return null;

  return (
    <ClearFiltersStyled onClick={onClick}>
      <CrossStyled />
      Clear All Filters
    </ClearFiltersStyled>
  );
};

const ClearFiltersStyled = styled.div`
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 13px;
  color: #ff5000;
`;

const CrossStyled = styled.div`
  margin-right: 5px;

  position: relative;
  cursor: pointer;
  width: 15px;
  height: 15px;
  margin-left: 10px;

  &:before {
    content: '';
    display: block;
    width: 90%;
    height: 2px;
    border-radius: 1px;
    background-color: #ff5000;

    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-45deg);
  }

  &:after {
    content: '';
    display: block;
    width: 90%;
    height: 2px;
    border-radius: 1px;
    background-color: #ff5000;

    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(45deg);
  }
`;

export default ClearFilters;
