import React from 'react';
import styled from 'styled-components';

interface IProps {
  onClick: () => void;
  isActive: boolean;
  order: 1 | 0;
}

const Sort: React.FC<IProps> = ({
  children,
  onClick,
  isActive,
  order,
}) => (
  <ContainerStyled onClick={onClick}>
    {children}
    <SortStyled>
      <ArrowStyledTop isActive={isActive && order === 1} />
      <ArrowStyledBottom isActive={isActive && order === 0} />
    </SortStyled>
  </ContainerStyled>
);

const ContainerStyled = styled.div`
  display: flex;
  align-items: center;
  cursor: pointer;
`;

const SortStyled = styled.div`
  margin-left: 10px;
`;

const ArrowStyledTop = styled.div<{ isActive: boolean }>`
  width: 11px;
  height: 11px;
  mask-image: url('/assets/sort.svg');
  mask-position: center;
  mask-repeat: no-repeat;
  mask-size: contain;
  background-color: ${({ isActive }) => (isActive ? '#f36621' : '#c4c4c4')};
  margin-bottom: 1px;
`;

const ArrowStyledBottom = styled(ArrowStyledTop)`
  transform: rotate(180deg);
  margin-bottom: 0px;
`;

export default Sort;
