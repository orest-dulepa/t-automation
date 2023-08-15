import React, { useEffect, useState } from 'react';
import moment from 'moment';

import { formatSeconds } from '@/utils/format-seconds';

const getDuration = (time: string) => {
  const currentTime = moment();
  const differenceInSeconds = currentTime.diff(time, 'seconds');

  return formatSeconds(differenceInSeconds);
};

interface IProps {
  startTime: string | null;
}

const Duration: React.FC<IProps> = ({ startTime }) => {
  const [time, setTime] = useState<string>();

  let interval: number;

  useEffect(() => {
    if (!startTime) return undefined;

    if (!interval) {
      interval = setInterval(() => {
        const value = getDuration(startTime);
        setTime(value);
      }, 1000);
    }

    return () => {
      clearInterval(interval);
    };
  }, [startTime]);

  if (!startTime) return <>-</>;

  return <>{time}</>;
};

export default Duration;
