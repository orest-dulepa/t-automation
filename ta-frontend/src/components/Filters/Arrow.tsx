import React from 'react';
import styled from 'styled-components';

interface IProps {
  isOpen: boolean;
}

const Arrow: React.FC<IProps> = ({ isOpen }) => <ArrowStyled isOpen={isOpen} />;

const ArrowStyled = styled.div<{ isOpen: boolean }>`
  width: 20px;
  min-width: 20px;
  height: 20px;
  min-height: 20px;
  margin-left: 25px;
  background-image: url('/assets/chevron.svg');
  background-position: center;
  background-size: contain;
  background-repeat: no-repeat;
  transform: ${({ isOpen }) => (isOpen ? 'rotate(90deg)' : 'rotate(-90deg)')};
  transition: 0.2s;
`;

export default Arrow;
