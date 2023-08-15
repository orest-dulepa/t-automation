import React from 'react';
import styled from 'styled-components';

import useInput from '@/components/common/hooks/useInput';
import Input from '@/components/common/Input';

interface IProps {
  onChange: (value: string) => void;
}

const InputFilter: React.FC<IProps> = ({ onChange }) => {
  const [value, setValue] = useInput('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    onChange(value);
    setValue('');
  };

  return (
    <InputWrapperStyled onSubmit={handleSubmit}>
      <InputStyled placeholder="Input" value={value} onChange={setValue} />
    </InputWrapperStyled>
  );
};

const InputWrapperStyled = styled.form``;

const InputStyled = styled(Input)`
  height: auto;
  min-width: 70px;
  padding: 10px 16px;

  transition: 0s;

  &::placeholder {
    font-size: 16px;
    color: #8b88a2;
  }
`;

export default InputFilter;
