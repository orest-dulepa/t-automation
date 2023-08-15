import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

import Logo from '@/components/common/Logo';

const Sidebar: React.FC = () => (
  <SidebarStyled>
    <Link to="/processes">
      <Logo />
    </Link>
  </SidebarStyled>
);

const SidebarStyled = styled.div`
  min-height: 100vh;
  background-color: white;
  min-width: 72px;
`;

export default Sidebar;
