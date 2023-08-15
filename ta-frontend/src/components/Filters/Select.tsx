import React, { useEffect, useState, useRef } from 'react';
import styled from 'styled-components';

import Arrow from './Arrow';

interface IProps {
  current: string | number;
  list: { title: string | number; value: string | number }[];
  onChange: (value: string) => void;
}

const Select: React.FC<IProps> = ({ current, list, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    document.addEventListener('click', handleClickOutside, true);

    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  }, []);

  const select = useRef<HTMLDivElement>(null);

  const handleClickOutside: EventListener = (e) => {
    const { target } = e;

    if (!select.current!.contains(target as Node)) {
      setIsOpen(false);
    }
  };

  const handleSelectClick = (e: React.MouseEvent) => {
    e.stopPropagation();

    setIsOpen(!isOpen);
  };

  const handleRowClick = (id: string) => (e: React.MouseEvent) => {
    e.stopPropagation();

    onChange(id);
    setIsOpen(false);
  };

  return (
    <SelectStyled ref={select}>
      <SelectCurrentStyled
        className={isOpen ? 'active' : 'inactive'}
        onClick={handleSelectClick}
        isOpen={isOpen}
      >
        <CurrentTextStyled>{current}</CurrentTextStyled>
        <Arrow isOpen={isOpen} />
      </SelectCurrentStyled>
      {isOpen && (
        <SelectListStyled>
          {list.map(({ title, value }) => (
            <SelectRow key={value} onClick={handleRowClick(String(value))}>
              <TextStyled>{title}</TextStyled>
            </SelectRow>
          ))}
        </SelectListStyled>
      )}
    </SelectStyled>
  );
};

const SelectStyled = styled.div`
  position: relative;
  min-width: 80px;
`;

const SelectCurrentStyled = styled.div<{ isOpen: boolean; }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 15px;
  border: 1px solid #ebedf2;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  border-color: ${({ isOpen }) => (isOpen ? '#ff5000' : '#ebedf2')};
`;

const TextStyled = styled.div`
  font-size: 16px;
  color: #495057;
  white-space: nowrap;
  width: 100%;
`;

const CurrentTextStyled = styled(TextStyled)`
  color: #8b88a2;
`;

const SelectListStyled = styled.div`
  position: absolute;
  top: calc(100% + 1px);
  left: 0px;
  z-index: 10;
  min-width: 100%;
  width: auto;
  border: 1px solid #f1f2f6;
  border-radius: 4px;
  background-color: white;

  border-radius: 11px;
  top: 100%;
  border-top-left-radius: unset;
  border-top-right-radius: unset;
  border-top: none;
  max-height: 270px;
  overflow: auto;

  >div {
    padding: 0px 6px;
    height: 42px;
    line-height: 42px;
    border-bottom: none;

    :hover {
      background-color: transparent;
      transition: none;
    }

    >div {
      padding-left: 43px;
      font-weight: 500;
      color: #656565;

      :hover {
        background: #E26F37;
        color: #ffffff;
        border-radius: 9px;
        transition: 0.15s;
      }
    }
  }
`;

const SelectRow = styled.div`
  min-width: 100%;
  padding: 10px;
  border-bottom: 1px solid #ebedf2;
  cursor: pointer;

  &:last-child {
    border-bottom: 0px;
  }

  &:hover {
    background-color: rgba(241, 242, 246, 0.25);
    transition: 0.15s;
  }
`;

export default Select;
