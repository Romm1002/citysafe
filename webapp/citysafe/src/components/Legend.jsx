import styles from '../styles/Legend.module.scss';

export default function Legend() {
  return (
    <div className={styles.legend}>
      <div className={styles.section}>
        <h4 className={styles.heading}>Densité (heatmap)</h4>
        <div className={styles.gradient} />
        <div className={styles.labels}>
          <span>Faible</span>
          <span>Élevée</span>
        </div>
      </div>

      <div className={styles.section}>
        <h4 className={styles.heading}>Nombre de crimes</h4>
        <div className={styles.item}>
          <span className={styles.marker} style={{ background: '#51bbd6' }} />
          <span>1-50</span>
        </div>
        <div className={styles.item}>
          <span className={styles.marker} style={{ background: '#f1f075' }} />
          <span>50-200</span>
        </div>
        <div className={styles.item}>
          <span className={styles.marker} style={{ background: '#f28cb1' }} />
          <span>200 +</span>
        </div>
      </div>
    </div>
  );
}
