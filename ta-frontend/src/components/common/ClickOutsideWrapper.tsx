import React, { useEffect, useRef } from 'react';

interface IProps {
  handleClose: (e: Event) => void;
}

const ClickOutsideWrapper: React.FC<IProps> = ({ handleClose, ...props }) => {
  useEffect(() => {
    document.addEventListener('click', handleClickOutside, true);

    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  }, []);

  const wrapper = useRef<HTMLDivElement>(null);

  const handleClickOutside: EventListener = (e) => {
    const { target } = e;

    if (!wrapper.current!.contains(target as Node)) {
      handleClose(e);
    }
  };

  return (
    <div ref={wrapper} {...props} />
  );
};

export default ClickOutsideWrapper;
