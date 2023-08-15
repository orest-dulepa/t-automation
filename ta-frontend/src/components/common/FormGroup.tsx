import React from 'react';
import styled from 'styled-components';
import { PropertyType } from '@/interfaces/process';

interface IProps extends ILabelStyledProps{
  label: string;
}

interface ILabelStyledProps {
  mandatory?: boolean;
  type?: PropertyType;
}

const FormGroup: React.FC<IProps> = ({
  label, mandatory, type, children,
}) => (
  <FormGroupStyled>
    <LabelStyled mandatory={mandatory} type={type}>{label}</LabelStyled>
    {children}
  </FormGroupStyled>
);

const FormGroupStyled = styled.label`
  display: block;
  margin-bottom: 16px;
`;

const LabelStyled = styled.div<ILabelStyledProps>`
  ${({ mandatory, type }) => mandatory && type !== PropertyType.RADIO && type !== PropertyType.CHECKBOX && `
    &:before {
      content: "* ";
      color: #EE4B2B;
    }
  `}
  text-transform: uppercase;
  color: #83839c;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
`;

export default FormGroup;
