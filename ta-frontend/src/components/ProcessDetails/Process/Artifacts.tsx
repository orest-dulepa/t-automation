import React, { useState } from 'react';
import styled from 'styled-components';

import { IUserProcessDetails } from '@/interfaces/user-process';

import Table from '@/components/common/Table';
import TableHead from '@/components/common/TableHead';
import TableData from '@/components/common/TableData';

import Pagination from './Pagination';

interface IProps extends Pick<IUserProcessDetails, 'artifacts'> {
  downloadArtifact: (key: string) => () => void;
  isArtifactDownloading: boolean;
}

const Artifacts: React.FC<IProps> = ({ downloadArtifact, artifacts, isArtifactDownloading }) => {
  const [currentList, setCurrentList] = useState<typeof artifacts>([]);

  const humanizeKeyName = (key: string) => {
    const [, name] = key.split('/');

    return name;
  };

  const formatSize = (num: number) => {
    try {
      switch (true) {
        case num > 999999: {
          return `${parseFloat((num / 1000000).toFixed(1))} mb`;
        }
        case num > 999: {
          return `${parseFloat((num / 1000).toFixed(1))} kb`;
        }
        default: {
          return `${num} b`;
        }
      }
    } catch (e) {
      console.log(e);

      return num;
    }
  };

  const isEmpty = !artifacts?.length;

  return (
    <>
      <Table name="Run artifacts" isEmpty={isEmpty} isMinorLoading={isArtifactDownloading} emptyText="No artifacts">
        <TableHead>
          <tr>
            <th>Name</th>
            <th>Size</th>
          </tr>
        </TableHead>

        <tbody>
          {currentList!.map(({ key, size }, i) => (
            <tr key={i}>
              <TableData onClick={downloadArtifact(key!)}>
                <ArtifactLinkStyled>{humanizeKeyName(key!)}</ArtifactLinkStyled>
              </TableData>
              <TableData>{formatSize(size!)}</TableData>
            </tr>
          ))}
        </tbody>
      </Table>

      {!isEmpty && <Pagination list={artifacts!} setCurrentList={setCurrentList} />}
    </>
  );
};

const ArtifactLinkStyled = styled.div`
  display: inline-block;
  color: #f36621;
  cursor: pointer;

  &:hover {
    color: #bd450a;
    text-decoration: underline;
  }
`;

export default Artifacts;
