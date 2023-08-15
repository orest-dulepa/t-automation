import React from 'react';
import styled from 'styled-components';

interface IProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {}

const Anchor: React.FC<IProps> = (props) => (
  <AnchorStyled rel="nofollow noopener noreferrer" target="_blank" {...props} />
);

const AnchorStyled = styled.a`
  color: #f36621;
  text-decoration: none;
  background-color: transparent;
  outline: none;

  &:hover {
    color: #bd450a;
    text-decoration: underline;
  }
`;

export default Anchor;
