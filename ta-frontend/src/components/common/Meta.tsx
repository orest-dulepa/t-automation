import React from 'react';
import styled from 'styled-components';

import { IPropertyWithValue } from '@/interfaces/process';

interface IProps {
  meta: IPropertyWithValue[];
}

const Meta: React.FC<IProps> = ({ meta }) => {
  if (!meta) return <>No meta info was provided</>;

  const truncate = (source: string, size: number) => (source.length > size ? `${source.slice(0, size - 1)}…` : source);

  const getFormattedValue = (value: string) => {
    try {
      let formattedValue = JSON.parse(value);

      if (Array.isArray(formattedValue)) {
        formattedValue = formattedValue.join(', ');
      }
      return truncate(formattedValue, 30);
    } catch {
      return truncate(value, 30);
    }
  };

  return (
    <>
      {meta.map(({ name, value, api_name }) => (
        <RowStyled key={api_name}>
          <MetaNameStyled>
            {name}
            :
          </MetaNameStyled>
          { getFormattedValue(value) }
        </RowStyled>
      ))}
    </>
  );
};

const RowStyled = styled.div`
  display: flex;
  align-items: center;
`;

const MetaNameStyled = styled.span`
  font-size: 12px;
  color: #8b88a2;
  margin-right: 7.5px;
`;

export default Meta;
