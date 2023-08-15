import React from 'react';
import ReactDOM from 'react-dom';
import styled from 'styled-components';

interface IProps {
  onBackdropClick: () => void;
  verticallyCentered?: boolean;
}

const Modal: React.FC<IProps> = ({ onBackdropClick, children, verticallyCentered }) => {
  const container = document.getElementById('root')!;

  const stopPropagation = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return ReactDOM.createPortal(
    <ModalStyled onClick={onBackdropClick} verticallyCentered={verticallyCentered}>
      <ModalBody onClick={stopPropagation} verticallyCentered={verticallyCentered}>
        <ModalHeader>
          <div onClick={onBackdropClick} />
        </ModalHeader>
        {children}
      </ModalBody>
    </ModalStyled>,
    container,
  );
};

const ModalStyled = styled.div<{verticallyCentered?: boolean}>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  background-color: rgba(25, 46, 67, 0.5);
  cursor: pointer;
  display: flex;
  align-items: ${({ verticallyCentered }) => (verticallyCentered ? 'center' : 'start')};
`;

const ModalBody = styled.div<{verticallyCentered?: boolean}>`
  max-width: fit-content;
  margin: ${({ verticallyCentered }) => (verticallyCentered ? '0 auto' : '30px auto 0px')};
  background-color: #fff;
  border: 1px solid #F1F2F6;
  border-radius: 3px;
  cursor: default;
`;

const ModalHeader = styled.div`
  height: 40px;
  width: 100%;
  padding: 8px 8px 8px 0;
  display: flex;
  justify-content: flex-end;
  background-color: #F1F2F6;

  div {
    width: 24px;
    height: 24px;
    mask-image: url('/assets/cancel.svg');
    mask-position: center;
    mask-repeat: no-repeat;
    mask-size: 50%;
    background-color: #000;
    cursor: pointer;
  }
`;

export default Modal;
