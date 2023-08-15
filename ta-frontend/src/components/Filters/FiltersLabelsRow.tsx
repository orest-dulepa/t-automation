import React from 'react';
import styled from 'styled-components';

import { FiltersFields } from '@/interfaces/filter';

interface IProps {
  filtersLabels: { title: string; filter: FiltersFields; value: string }[];
  removeFilter: (query: FiltersFields, value: string) => void;
}

const FiltersLabelsRow: React.FC<IProps> = ({ filtersLabels, removeFilter }) => {
  const handleClick = (query: FiltersFields, value: string) => () => {
    removeFilter(query, value);
  };

  return (
    <FiltersLabelsRowStyled>
      {filtersLabels.map(({ title, filter, value }, i) => (
        <LabelStyled key={i}>
          {title}
          <CrossStyled onClick={handleClick(filter, value)} />
        </LabelStyled>
      ))}
    </FiltersLabelsRowStyled>
  );
};

const FiltersLabelsRowStyled = styled.div`
  display: flex;
  flex-wrap: wrap;
`;

const LabelStyled = styled.div`
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: #ffffff;
  border: 1px solid #f1f2f6;
  border-radius: 10px;
  font-size: 16px;
  color: #8b88a2;
  margin: 15px 10px 0px 0px;
`;

const CrossStyled = styled.div`
  position: relative;
  cursor: pointer;
  width: 20px;
  height: 20px;
  margin-left: 10px;

  &:before {
    content: '';
    display: block;
    width: 90%;
    height: 2px;
    border-radius: 1px;
    background-color: #8b88a2;

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
    background-color: #8b88a2;

    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(45deg);
  }
`;

export default FiltersLabelsRow;
