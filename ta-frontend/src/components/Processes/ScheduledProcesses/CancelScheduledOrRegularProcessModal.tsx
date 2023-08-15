import React from 'react';
import styled from 'styled-components';

import Button from '@/components/common/Button';
import Error from '@/components/common/Error';

interface IProps {
  isScheduled?: boolean;
  onClose: () => void;
  onDelete: () => void;
  isPending: boolean;
  isRejected: boolean;
}

const CancelScheduledOrRegularProcessModal: React.FC<IProps> = ({
  isScheduled, onClose, onDelete, isPending, isRejected,
}) => (
  <CancelModal>
    <div>
      <p>
        Are you sure you want to delete the
        { isScheduled ? ' scheduled ' : ' regular ' }
        process?
      </p>
      <p>You can’t undo this action.</p>
    </div>
    <ButtonWrapper>
      <Cancel disabled={isPending} onClick={onClose}>Cancel</Cancel>
      <Delete disabled={isPending} onClick={onDelete}>
        { isPending ? 'Loading' : 'Delete' }
      </Delete>
    </ButtonWrapper>

    {isRejected && <Error>Something went wrong :(</Error>}
  </CancelModal>
);

const CancelModal = styled.div`
  position: relative;
  max-width: 384px;
  height: 380px;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  margin: 20px;

  p {
    text-align: center;
  }

  p:first-of-type {
    font-weight: 500;
    font-size: 19px;
    line-height: 22px;
    margin-bottom: 17px;
  }

  p:last-of-type {
    line-height: 19px;
    color: #AFAFC3;
  }
`;

const ButtonWrapper = styled.div`
  display: flex;
  justify-content: center;

  button {
    width: 100px;
    height: 35px;
  }

  button:first-of-type {
    margin-right: 20px;
  }
`;

const Cancel = styled(Button)`
  background-color: #AFAFC3;
  border-color: #AFAFC3;
`;

const Delete = styled(Button)``;

export default CancelScheduledOrRegularProcessModal;
