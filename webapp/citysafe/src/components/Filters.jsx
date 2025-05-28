import '../styles/Filters.scss';

export default function Filters({
  crimeTypes,
  selectedType,
  onTypeChange
}) {
  return (
    <div className="filters">
      <select
        id="crime-type-select"
        className="filter-select"
        value={selectedType}
        onChange={e => onTypeChange(e.target.value)}
      >
        <option value="">— Choisir un type de crime —</option>
        {crimeTypes.map(type => (
          <option key={type} value={type}>{type}</option>
        ))}
      </select>

      <input
        type="date"
        className="filter-date"
        aria-label="Filtrer par date"
      />

      <select className="filter-select" aria-label="Filtrer par arrondissement">
        <option value="">Tous les arrondissements</option>
        <option>Manhattan</option>
        <option>Brooklyn</option>
        <option>Queens</option>
        <option>Bronx</option>
        <option>Staten Island</option>
      </select>
    </div>
  );
}
