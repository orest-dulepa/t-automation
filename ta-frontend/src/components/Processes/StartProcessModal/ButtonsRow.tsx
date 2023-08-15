import React from 'react';
import styled from 'styled-components';

import Button from '@/components/common/Button';

interface IProps {
  handleCancel: () => void;
  isPending: boolean;
  submitContent: string;
}

const ButtonsRow: React.FC<IProps> = ({ handleCancel, isPending, submitContent }) => (
  <ButtonsRowStyled>
    <CTA disabled={isPending} type="button" onClick={handleCancel}>Cancel</CTA>
    <CTA isLoading={isPending} type="submit">{submitContent}</CTA>
  </ButtonsRowStyled>
);

const ButtonsRowStyled = styled.div`
  padding-top: 25px;
  display: flex;
  justify-content: flex-end;
`;

const CTA = styled(Button)`
  font-size: 14px;
  margin-left: 8px;

  &:first-child {
    margin-left: 0px;
  }
`;

export default ButtonsRow;
