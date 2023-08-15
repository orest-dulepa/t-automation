import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import moment from 'moment';
import { IProperty, PropertyDataDefaultValues, PropertyType } from '@/interfaces/process';
import FormGroup from '@/components/common/FormGroup';
import Input from '@/components/common/Input';
import Calendar from '@/components/common/Calendar';
import ClickOutsideWrapper from '@/components/common/ClickOutsideWrapper';
import Textarea from '@/components/common/Textarea';
import RadioAndCheckboxGroup from '@/components/common/RadioAndCheckboxGroup';
import Radio from '@/components/common/Radio';
import Checkbox from '@/components/common/Checkbox';

interface IProps extends IProperty {
  value: string;
  defaultVal: string;
  onChange: (value: string) => void;
}

const Property: React.FC<IProps> = (
  {
    name,
    api_name,
    type,
    value,
    mandatory,
    defaultVal,
    options,
    onChange,
  },
) => {
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  const [radioValue, setRadioValue] = useState('');
  const [checkboxValues, setCheckboxValues] = useState<Array<string>>([]);

  useEffect(() => {
    if (type === PropertyType.CHECKBOX) {
      onChange(JSON.stringify(checkboxValues));
    }
  }, [checkboxValues]);

  useEffect(() => {
    if (
      defaultVal
      && !(type === PropertyType.DATE && defaultVal in PropertyDataDefaultValues)
      && type !== PropertyType.RADIO
      && type !== PropertyType.CHECKBOX
    ) {
      onChange(defaultVal);
    }

    if (type === PropertyType.RADIO && options.length > 0) {
      if (defaultVal) {
        setRadioValue(defaultVal);
        onChange(defaultVal);
      } else {
        setRadioValue(options[0]);
        onChange(options[0]);
      }
    }

    if (type === PropertyType.CHECKBOX && options.length > 0 && defaultVal) {
      if (Array.isArray(defaultVal)) {
        setCheckboxValues(() => [...defaultVal]);
      }
    }
  }, [defaultVal]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { value: newValue } = e.target;

    if (type === PropertyType.RADIO && options.length > 0) {
      setRadioValue(newValue);
    }

    if (type === PropertyType.CHECKBOX && options.length > 0) {
      setCheckboxValues((prev) => {
        let checkedValues = prev;

        if (!checkedValues.includes(newValue)) {
          checkedValues.push(newValue);
        } else {
          checkedValues = prev.filter((val) => val !== newValue);
        }

        return [...checkedValues];
      });
    }

    if (type !== PropertyType.CHECKBOX) onChange(newValue);
  };

  const handleDateChange = (e: Date | Date[]) => {
    const newValue = moment(e as Date).format('MM/DD/YYYY');

    onChange(newValue);
    setIsCalendarOpen(false);
  };

  const handleDateOpen = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();

    setIsCalendarOpen(true);
  };

  const handleDateClose = (e: Event) => {
    e.stopPropagation();
    e.preventDefault();

    setIsCalendarOpen(false);
  };

  const renderInput = () => {
    switch (type) {
      case PropertyType.TEXT:
      case PropertyType.EMAIL:
        return (
          <InputStyled
            placeholder="Enter data"
            required={mandatory}
            type={type}
            value={value}
            onChange={handleInputChange}
          />
        );
      case PropertyType.RADIO:
        return (
          <>
            {
              options.map((option, index) => (
                <RadioAndCheckboxGroup key={`checkbox-${index}`}>
                  <Radio
                    id={`checkbox-option-${index}`}
                    name={api_name}
                    type="radio"
                    value={option}
                    checked={radioValue === option}
                    onChange={handleInputChange}
                  />
                  <label htmlFor={`checkbox-option-${index}`} style={{ cursor: 'pointer' }}>{option}</label>
                </RadioAndCheckboxGroup>
              ))
            }
          </>
        );
      case PropertyType.CHECKBOX:
        return (
          <>
            {
              options.map((option, index) => (
                <RadioAndCheckboxGroup key={index}>
                  <Checkbox
                    id={`radio-option-${index}`}
                    name={api_name}
                    type="checkbox"
                    value={option}
                    checked={checkboxValues.includes(option)}
                    onChange={handleInputChange}
                  />
                  <label htmlFor={`radio-option-${index}`} style={{ cursor: 'pointer' }}>{option}</label>
                </RadioAndCheckboxGroup>
              ))
            }
          </>
        );
      case PropertyType.TEXTAREA:
        return (
          <TextareaStyled
            placeholder="Enter data"
            required={mandatory}
            value={value}
            onChange={handleInputChange}
          />
        );
      case PropertyType.DATE:
        return (
          <>
            <CalendarDateStyled isEmpty={!value} onClick={handleDateOpen} isOpen={isCalendarOpen}>
              { value || 'MM/DD/YYYY' }
              {
                isCalendarOpen && (
                  <CalendarWrapperStyled
                    handleClose={handleDateClose}
                  >
                    <Calendar
                      handleChange={handleDateChange}
                      // Moment crashes if value is an empty string, but works if it is undefined
                      value={moment(value || undefined).toDate()}
                    />
                  </CalendarWrapperStyled>
                )
              }
            </CalendarDateStyled>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <PropertyStyled>
      <FormGroup label={name} mandatory={mandatory} type={type}>{renderInput()}</FormGroup>
    </PropertyStyled>
  );
};

const PropertyStyled = styled.div`
  label div {
    color: #656565;
  }
`;

const inputAndTextareaStyles = `
  padding: 10px 16px;
  height: initial;

  ::placeHolder {
    color: #c4c4c4;
  }
`;
const InputStyled = styled(Input)`${inputAndTextareaStyles}`;
const TextareaStyled = styled(Textarea)`${inputAndTextareaStyles}`;

const CalendarDateStyled = styled.div<{ isEmpty: boolean, isOpen: boolean }>`
  display: block;
  width: 100%;
  padding: 10px 16px;
  min-height: 46px;
  font-size: 1rem;
  line-height: 1.5;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid #ebedf2;
  border-radius: 4px;
  position: relative;
  cursor: pointer;

  color: ${({ isEmpty }) => (isEmpty ? '#6c757d' : '#495057')};
  border-color: ${({ isOpen }) => (isOpen ? '#ff5000' : '#ebedf2')};
`;

const CalendarWrapperStyled = styled(ClickOutsideWrapper)`
  position: absolute;
  top: calc(100% + 2px);
  left: 0px;
  z-index: 10;
`;

export default Property;
