import { forwardRef } from 'react';
import styles from '../styles/Tooltip.module.scss';

export default forwardRef(function Tooltip(_, ref) {
  return <div ref={ref} className={styles.tooltip} />;
});
