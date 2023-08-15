import React from 'react';
import styled from 'styled-components';

interface IProps {
  errorMsg: string;
}

const Error: React.FC<IProps> = ({ errorMsg }) => (
  <ErrorStyled>
    <EmojiStyled />
    <MsgStyled>{errorMsg}</MsgStyled>
  </ErrorStyled>
);

const ErrorStyled = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
`;

const EmojiStyled = styled.div`
  width: 90px;
  height: 90px;
  margin-bottom: 15px;
  background-image: url('/assets/emoji-eye-roll.png');
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
`;

const MsgStyled = styled.div`
  max-width: 350px;
  font-size: 18px;
  font-weight: bold;
  text-align: center;
  padding: 10px;
  background-color: white;
  border-radius: 6px;
  border: 1px solid #f1f2f6;
`;

export default Error;
