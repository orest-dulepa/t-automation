import React from 'react';
import styled from 'styled-components';

interface IProps {
  isToggleOn: boolean;
  handleToggleState: () => void;
}

const ToggleSwitch: React.FC<IProps> = ({ isToggleOn, handleToggleState }) => (
  <Toggler className={isToggleOn ? 'active' : 'inactive'} onClick={handleToggleState}>
    <SwitchCircle />
  </Toggler>
);

const Toggler = styled.div`
  position: relative;
  width: 38px;
  height: 14px;
  background-color: #E5E5E5;
  border-radius: 7px;
  cursor: pointer;

  &.active {
    background-color: rgba(226,111,55,0.24);

    >div {
      background-color: #E16F37;
      right: 0;
    }
  }
`;

const SwitchCircle = styled.div`
  position: absolute;
  width: 22px;
  height: 22px;
  top: -4px;
  background-color: #ACACAC;
  border-radius: 50px;
`;

export default ToggleSwitch;
