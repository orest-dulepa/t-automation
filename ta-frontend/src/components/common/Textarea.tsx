import React from 'react';
import styled from 'styled-components';

interface IProps extends React.InputHTMLAttributes<HTMLTextAreaElement> {}

const Textarea: React.FC<IProps> = (props) => <TextareaStyled {...props} />;

const TextareaStyled = styled.textarea`
  display: block;
  width: 100%;
  min-height: 100px;
  max-height: 600px;
  padding: 20px 16px;
  font-size: 1rem;
  font-weight: 16px;
  line-height: 1.5;
  color: #495057;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid #ebedf2;
  border-radius: 4px;
  outline: none;
  resize: vertical;

  &::placeholder {
    color: #6c757d;
    opacity: 1;
  }

  &:focus {
    color: #495057;
    background-color: #fff;
    border-color: #ff5000;
    outline: 0;
    box-shadow: none;
  }

  &:read-only {
    background-color: #e9ecef;
  }
`;

export default Textarea;
