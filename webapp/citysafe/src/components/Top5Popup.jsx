import styles from '../styles/Top5Popup.module.scss';

export default function Top5Popup({ title, items, onClose }) {
  if (!items || items.length === 0) return null;

  return (
    <div className={styles.popup}>
      <button className={styles.close} onClick={onClose}>×</button>
      <h3 className={styles.title}>{title}</h3>
      <ul className={styles.list}>
        {items.map(({ neighborhood_id, name, boro, count }) => (
          <li key={neighborhood_id} className={styles.item}>
            <strong>{name}</strong> ({boro}) : {count}
          </li>
        ))}
      </ul>
    </div>
  );
}
