import React from 'react';
import styled from 'styled-components';

import Select from './Select';

interface IProps {
  currentItemsPerPage: number;
  onChange: (amount: number) => void;
}

const ItemsPerPage: React.FC<IProps> = ({ currentItemsPerPage, onChange }) => {
  const handleOnChange = (amount: string | number) => {
    onChange(amount as number);
  };

  return (
    <ItemsPerPageStyled>
      <TextStyled>Items Per Page</TextStyled>
      <Select
        current={currentItemsPerPage}
        list={[
          { title: 10, value: 10 },
          { title: 20, value: 20 },
          { title: 30, value: 30 },
          { title: 40, value: 40 },
          { title: 50, value: 50 },
        ]}
        onChange={handleOnChange}
      />
    </ItemsPerPageStyled>
  );
};

const ItemsPerPageStyled = styled.div`
  display: flex;
  align-items: center;
  padding-right: 40px;
`;

const TextStyled = styled.div`
  font-size: 16px;
  color: #8b88a2;
  margin-right: 10px;
`;

export default ItemsPerPage;
