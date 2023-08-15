import React from 'react';
import styled from 'styled-components';

const Logo: React.FC = () => <LogoStyled />;

const LogoStyled = styled.div`
  width: 72px;
  height: 72px;
  background-image: url('/assets/logo.svg');
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
`;

export default Logo;
