import React, { useLayoutEffect, useRef, useState } from 'react';

// Mount charts only after their parent has a measurable layout. This avoids
// negative initial dimensions when changing routes or opening the mobile menu.
export const ChartContainer = ({ children, width = '100%', height = '100%' }) => {
  const ref = useRef(null);
  const [size, setSize] = useState(null);
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    const update = () => {
      const { width, height } = element.getBoundingClientRect();
      if (width > 0 && height > 0) {
        setSize(previous => previous?.width === width && previous?.height === height ? previous : { width, height });
      }
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return <div ref={ref} style={{ width, height, minWidth: 0, overflow: 'hidden' }}>
    {size && React.cloneElement(children, size)}
  </div>;
};