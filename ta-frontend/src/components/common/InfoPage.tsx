import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

import Logo from '@/components/common/Logo';

interface IProps {
  title: string;
  subtitle: string;
}

const InfoPage: React.FC<IProps> = ({ title, subtitle, children }) => (
  <InfoPageStyled>
    <HeaderStyled>
      <Link to="/">
        <Logo />
      </Link>
    </HeaderStyled>

    <ContentWrapperStyled>
      <HeadRowStyled>
        <HeadTitleStyled>{title}</HeadTitleStyled>
        <HeadSubtitleStyled>{subtitle}</HeadSubtitleStyled>
      </HeadRowStyled>

      {children}
    </ContentWrapperStyled>
  </InfoPageStyled>
);

const InfoPageStyled = styled.div`
  padding: 0px 0px 50px;
`;

const ContentWrapperStyled = styled.div`
  max-width: 1024px;
  margin: 0px auto;
  padding: 0px 10px;
  font-size: 14px;
`;

const HeaderStyled = styled.header`
  margin-bottom: 50px;
`;

const HeadRowStyled = styled.div`
  margin-bottom: 50px;
`;

const HeadTitleStyled = styled.h1`
  font-size: 26px;
  margin-bottom: 10px;
  color: #000000;
`;

const HeadSubtitleStyled = styled.div`
  color: #595959;
  font-size: 14px;
`;

export default InfoPage;
