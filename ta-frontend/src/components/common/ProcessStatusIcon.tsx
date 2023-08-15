import React from 'react';
import styled, { keyframes } from 'styled-components';
import { ProcessStatus } from '@/interfaces/user-process';

type Statuses = 'run' | 'flashing' | 'success' | 'error' | 'warning' | 'scheduled' | 'regular';

interface IProps {
  status?: ProcessStatus;
}

const ProcessStatusIcon: React.FC<IProps> = ({ status }) => {
  const getIndicator = (): Statuses => {
    switch (status) {
      case ProcessStatus.FINISHED: {
        return 'success';
      }
      case ProcessStatus.FAILED: {
        return 'error';
      }
      case ProcessStatus.WARNING: {
        return 'warning';
      }
      case ProcessStatus.SCHEDULED: {
        return 'scheduled';
      }
      case ProcessStatus.REGULAR: {
        return 'regular';
      }
      default: {
        return 'flashing';
      }
    }
  };

  return (
    <WrapperStyled className={getIndicator()}>
      <div />
    </WrapperStyled>
  );
};

const blinker = keyframes`
  50% {
    opacity: 0.3;
  }
`;

const WrapperStyled = styled.div`
  width: 30px;
  min-width: 30px;
  height: 30px;
  min-height: 30px;
  border-radius: 50%;
  display: inline-flex;
  position: relative;
  align-items: center;
  justify-content: center;

  &.run {
    background-color: #f9fafc;

    > div {
      width: 8px;
      height: 8px;
      background: #afafc6;
      border-radius: 50%;
    }
  }

  &.scheduled {
    background-color: rgba(255, 212, 62, 0.4);

    > div {
      width: 18px;
      height: 18px;
      mask-image: url('/assets/clock.svg');
      mask-position: center;
      mask-repeat: no-repeat;
      mask-size: contain;
      background-color: #FFB422;
    }
  }
  
  &.regular {
    background-color: rgba(106, 61, 255, 0.2);

    > div {
      width: 18px;
      height: 18px;
      mask-image: url('/assets/regular-clock.svg');
      mask-position: center;
      mask-repeat: no-repeat;
      mask-size: contain;
      background-color: rgba(106, 61, 255, 1);
    }
  }

  &.flashing {
    background-color: rgba(206, 240, 220, 0.4);
    animation: ${blinker} 2s linear infinite;

    > div {
      width: 8px;
      height: 8px;
      background: #34ad66;
      border-radius: 50%;
    }
  }

  &.success {
    background-color: rgba(206, 240, 220, 0.4);

    > div {
      width: 18px;
      height: 14px;
      background-image: url('/assets/checkmark.svg');
      background-position: center center;
      background-size: contain;
      background-repeat: no-repeat;
    }
  }

  &.error {
    background-color: rgba(215, 45, 45, 0.1);

    > div {
      width: 13px;
      height: 13px;
      background-image: url('/assets/cancel.svg');
      background-position: center center;
      background-size: contain;
      background-repeat: no-repeat;
    }
  }
  
  &.warning {
    background-color: rgba(255, 204, 0, 0.2);

    > div {
      width: 18px;
      height: 18px;
      background-image: url('/assets/warning.svg');
      background-position: center center;
      background-size: contain;
      background-repeat: no-repeat;
    }
  }
`;

export default ProcessStatusIcon;
