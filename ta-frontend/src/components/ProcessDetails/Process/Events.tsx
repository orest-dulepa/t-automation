import React, { useState } from 'react';

import { IUserProcessDetails } from '@/interfaces/user-process';

import Table from '@/components/common/Table';
import TableHead from '@/components/common/TableHead';
import TableData from '@/components/common/TableData';
import Time from '@/components/common/Time';

import Pagination from './Pagination';

interface IProps extends Pick<IUserProcessDetails, 'events'> {}

const Events: React.FC<IProps> = ({ events }) => {
  const [currentList, setCurrentList] = useState<typeof events>([]);

  const isEmpty = !events.length;

  return (
    <>
      <Table name="Events" isEmpty={isEmpty} emptyText="No events">
        <TableHead>
          <tr>
            <th>Event category</th>
            <th>Timestamp</th>
          </tr>
        </TableHead>

        <tbody>
          {currentList.map(({ eventType, timeStamp }, i) => (
            <tr key={i}>
              <TableData>{eventType}</TableData>
              <TableData>
                <Time time={timeStamp} />
              </TableData>
            </tr>
          ))}
        </tbody>
      </Table>

      {!isEmpty && <Pagination list={events} setCurrentList={setCurrentList} />}
    </>
  );
};

export default Events;
