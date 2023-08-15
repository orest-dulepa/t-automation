import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

import Anchor from '@/components/common/Anchor';
import Logo from '@/components/common/Logo';

const NotFound: React.FC = () => (
  <NotFoundStyled>
    <HeaderStyled>
      <Link to="/">
        <Logo />
      </Link>

      <BotsLinkStyled to="/processes">View bots</BotsLinkStyled>
    </HeaderStyled>

    <ContentStyled>
      <TitleStyled>Oops! Something isn’t right here.</TitleStyled>
      <DescriptionStyled>Please give it another go or contact support</DescriptionStyled>
    </ContentStyled>

    <FooterStyled>
      Having trouble signing in?
      {' '}
      <Anchor href="mailto:support@ta.com">Contact us</Anchor>
    </FooterStyled>
  </NotFoundStyled>
);

const NotFoundStyled = styled.div`
  padding: 30px;
  background: url('/assets/404.svg') no-repeat 50% 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
`;

const HeaderStyled = styled.header`
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
`;

const BotsLinkStyled = styled(Link)`
  display: inline-block;
  margin: 26px 0;
  padding: 0 23px;
  font-weight: 500;
  color: #192e43;
  text-decoration: none;

  &:hover {
    color: #f36621;
    text-decoration: underline;
  }
`;

const ContentStyled = styled.div`
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

const TitleStyled = styled.div`
  font-weight: 500;
  font-size: 30px;
`;

const DescriptionStyled = styled.div``;

const FooterStyled = styled.footer`
  text-align: center;
`;

export default NotFound;
