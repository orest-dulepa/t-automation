import React, { useEffect, useState } from 'react';
import Select from '@/components/Filters/Select';
import { getTimelineLabels } from '@/utils/get-timeline-labels';
import styled from 'styled-components';

interface IDaysOfWeekProps {
  onChange: Function;
}

const RegularTime: React.FC<IDaysOfWeekProps> = ({ onChange }) => {
  const INTERVAL_IN_MINUTES = 30;
  const [selectedTime, setSelectedTime] = useState('12:00 AM');

  useEffect(() => {
    onChange(selectedTime);
  }, [selectedTime]);

  const timeForDropdown = () => {
    const timelineLabels = getTimelineLabels('00:00', INTERVAL_IN_MINUTES, 'm');

    return timelineLabels.map((timelineLabel) => ({ title: timelineLabel, value: timelineLabel }));
  };

  return (
    <RegularTimeStyled>
      <Select current={selectedTime} list={timeForDropdown()} onChange={setSelectedTime} />
    </RegularTimeStyled>
  );
};

const RegularTimeStyled = styled.div`
  >div {
    // width: 173px;

    >div:first-child {
      position: relative;
      padding: 12px 10px 12px 49px;
      border-color: #ebedf2;
      border-radius: 11px;

      &.active {
        border-bottom-left-radius: unset;
        border-bottom-right-radius: unset;
        border-bottom: none;
      }

      ::before {
        position: absolute;
        content: '';
        top: 12px;
        left: 10px;
        width: 24px;
        height: 24px;
        mask-image: url('/assets/clock.svg');
        mask-position: center;
        mask-repeat: no-repeat;
        mask-size : contain;
        background-color: #E26F37;
      }

      >div:first-of-type {
        font-weight: 500;
        color: #656565;
      }

      div[class*="ArrowStyled"] {
        width: 24px;
        min-width: 24px;
        height: 24px;
        min-height: 24px;
        mask-image: url('/assets/chevron.svg');
        mask-position: center;
        mask-size: contain;
        mask-repeat: no-repeat;
        background-color: #656565;
      }
    }
  }
`;

export default RegularTime;
