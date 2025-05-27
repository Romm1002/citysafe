import '../styles/CrimePopup.scss';

export default function CrimePopup({ neighborhood, onClose }) {
  if (!neighborhood) return null;

  return (
    <div className="neighborhood-popup">
      <button className="popup-close" onClick={onClose}>×</button>
      <h3>{neighborhood.NTAName}</h3>
      <p><strong>Arrondissement :</strong> {neighborhood.BoroName}</p>
      <p><strong>Code NTA :</strong> {neighborhood.NTA2020}</p>
    </div>
  );
}
