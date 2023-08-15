import React from 'react';
import styled from 'styled-components';

import GlobalLoader from '@/components/common/GlobalLoader';

interface IProps {
  handleTryReload?: () => void;
  name: string;
  isLoading?: boolean;
  isMinorLoading?: boolean;
  isError?: boolean;
  isEmpty?: boolean;
  emptyText?: string;
  isFixedHeight?: boolean;
  nameComponent?: React.ReactNode;
  component?: React.ReactNode;
}

const Table: React.FC<IProps> = ({
  handleTryReload,
  name,
  isLoading,
  isMinorLoading,
  isError,
  isEmpty,
  emptyText,
  children,
  isFixedHeight,
  nameComponent,
  component,
}) => {
  const renderBody = () => {
    switch (true) {
      case isLoading: {
        return (
          <InfoWrapper>
            <GlobalLoader />
          </InfoWrapper>
        );
      }
      case isError: {
        return (
          <ErrorStyled>
            Something went wrong :(
            <Try onClick={handleTryReload}>Try again</Try>
          </ErrorStyled>
        );
      }
      case isEmpty: {
        return (
          <InfoWrapper>
            <Info>{emptyText || 'No data'}</Info>
          </InfoWrapper>
        );
      }
      default: {
        return <TableStyled>{children}</TableStyled>;
      }
    }
  };

  return (
    <WrapperStyled>
      <TableName>
        {name}
        {nameComponent}
      </TableName>
      {component}
      <TableWrapperStyled isFixedHeight={isFixedHeight}>
        {isMinorLoading && (
          <MinorLoaderStyled>
            <GlobalLoader />
          </MinorLoaderStyled>
        )}
        {renderBody()}
      </TableWrapperStyled>
    </WrapperStyled>
  );
};

const WrapperStyled = styled.div`
  margin-bottom: 30px;
`;

const TableName = styled.h4`
  margin: 0px 0px 14px;
  font-size: 20px;
  font-weight: 500;
  line-height: 1;
  display: flex;
  align-items: center;
`;

const TableWrapperStyled = styled.div<{ isFixedHeight?: boolean }>`
  position: relative;
  border: 1px solid #f1f2f6;
  border-radius: 6px;
  overflow: ${({ isFixedHeight }) => (isFixedHeight ? 'auto' : 'hidden')};
  max-height: ${({ isFixedHeight }) => (isFixedHeight ? '75vh' : 'auto')};
`;

const InfoWrapper = styled.div`
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: white;
`;

const Info = styled.div`
  padding: 77px 0px 34px;
  background: #fff url('/assets/info.svg') no-repeat 50% 34px;
  text-align: center;
`;

const MinorLoaderStyled = styled.div`
  position: absolute;
  z-index: 1;
  top: 0px;
  left: 0px;
  right: 0px;
  bottom: 0px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.5);
`;

const ErrorStyled = styled.div`
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background-color: white;
  color: red;
`;

const Try = styled.div`
  color: #f36621;
  cursor: pointer;

  &:hover {
    color: #bd450a;
    text-decoration: underline;
  }
`;

const TableStyled = styled.table`
  transform-origin: top;
  border-style: hidden;
  box-shadow: 0 0 0 1px #f1f2f6;
  width: 100%;
  color: #212529;
  border-collapse: collapse;
`;

export default Table;
